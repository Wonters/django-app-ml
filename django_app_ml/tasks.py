import logging
import dramatiq
import pandas as pd
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from .logging import get_logger
from .ml import train, predict
from .dataset_audit import PandasDatasetAuditor
from .models import Bucket, AuditReport, DataSet, IARecommandation, MLFlowTemplate
from .exceptions import AuditDatasetException, DatasetNotFoundError, DatasetAccessError, DatasetValidationError
from .recommandation import get_ai_recommendations
from .schema.task import TaskResult
import tempfile

logger = get_logger(__name__)


@dramatiq.actor(queue_name="train",
                max_retries=0,
                min_backoff=1000,
                time_limit=60000*3,
                actor_name="ml_app.train_task",
                store_results=True)
def train_task(dataset_path: str, checkpoint: str = ""):
    """
    Call the model to train ini grpc 
    """
    logger.info(f"Train dataset: {dataset_path}, save on {checkpoint}")
    df_train = pd.read_parquet(dataset_path)
    result = train(df_train, checkpoint)
    return {
        'status': 'success',
        'checkpoint': checkpoint,
        'dataset_path': dataset_path,
        'result': result
    }


@dramatiq.actor(queue_name="predict",
                max_retries=0,
                actor_name="ml_app.predict_task",
                min_backoff=1000, 
                time_limit=60000*3,
                store_results=True)
def predict_task(checkpoint, client):
    result = predict(checkpoint, client)
    return {
        'status': 'success',
        'checkpoint': checkpoint,
        'client': client,
        'result': result
    }


@dramatiq.actor(queue_name="audit",
                max_retries=0,
                actor_name="ml_app.audit_task",
                min_backoff=1000, 
                time_limit=60000*5,
                store_results=True)
def audit_dataset_task(dataset_id: int, save_report: bool = True, report_path: str = None):
    """
    Effectue un audit complet d'un dataset avec Pandas
    """
    logger.info(f"Début de l'audit du dataset: {dataset_id}")
    try:
        dataset = DataSet.objects.get(id=dataset_id)
        # Vérifier si le bucket existe
        if dataset.bucket is not None:
            try:
                bucket_obj = Bucket.objects.get(id=dataset.bucket.id)
            except Bucket.DoesNotExist:
                logger.error(f"Bucket non trouvé avec l'ID: {dataset.bucket.id}")
                exception = DatasetNotFoundError(f"Bucket non trouvé avec l'ID: {dataset.bucket.id}")
                return TaskResult(error=True, message=str(exception)).dict()
        else:
            bucket_obj = None
            
        auditor = PandasDatasetAuditor(bucket_obj)
        results = auditor.full_audit(dataset.link, save_report=save_report, report_path=report_path)
        AuditReport.objects.create(dataset=dataset, report=results)
        logger.info(f"Audit terminé avec succès pour: {dataset.link}")
        return TaskResult(error=False, results=results, message='Audit terminé avec succès').dict()
        
    except FileNotFoundError as e:
        logger.error(f"Fichier dataset non trouvé: {dataset.link}")
        exception = DatasetNotFoundError(f"Fichier dataset non trouvé: {dataset.link}")
        return TaskResult(error=True, message=str(exception)).dict()
        
    except PermissionError as e:
        logger.error(f"Erreur de permission pour le dataset {dataset.link}: {e}")
        exception = DatasetAccessError(f"Erreur de permission pour le dataset {dataset.link}: {e}")
        return TaskResult(error=True, message=str(exception)).dict()
        
    except ValueError as e:
        logger.error(f"Erreur de validation du dataset {dataset.link}: {e}")
        exception = DatasetValidationError(f"Erreur de validation du dataset {dataset.link}: {e}")
        return TaskResult(error=True, message=str(exception)).dict()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'audit du dataset {dataset.link}: {e}")
        exception = AuditDatasetException(f"Erreur lors de l'audit du dataset {dataset.link}: {e}")
        return TaskResult(error=True, message=str(exception)).dict()


@dramatiq.actor(queue_name="analyse_ia",
                max_retries=0,
                actor_name="ml_app.analyse_ia_task",
                min_backoff=1000, 
                time_limit=60000*5,
                store_results=True)
def analyse_ia_task(dataset_id: int):
    """
    Effectue une analyse IA d'un dataset en utilisant les recommandations IA
    """
    logger.info(f"Début de l'analyse IA du dataset: {dataset_id}")
    try:
        dataset = DataSet.objects.get(id=dataset_id)
        
        # Récupérer le rapport d'audit le plus récent pour ce dataset
        try:
            latest_audit = AuditReport.objects.filter(dataset=dataset).latest('created_at')
            audit_report = latest_audit.report
            logger.info(f"Rapport d'audit trouvé pour le dataset {dataset_id}")
        except AuditReport.DoesNotExist:
            logger.error(f"Aucun rapport d'audit trouvé pour le dataset {dataset_id}")
            return TaskResult(error=True, message=f"Aucun rapport d'audit trouvé pour le dataset {dataset_id}. Veuillez d'abord effectuer un audit.").dict()
        
        # Générer les recommandations IA
        logger.info(f"Génération des recommandations IA pour le dataset {dataset_id}")
        try:
            ai_recommendations = get_ai_recommendations(audit_report)
            logger.info(f"Génération réussie de {len(ai_recommendations)} recommandations IA")
            IARecommandation.objects.create(dataset=dataset, recommendation=ai_recommendations)
        except Exception as ai_error:
            logger.error(f"Erreur lors de la génération des recommandations IA: {ai_error}")
            return TaskResult(error=True, message=f"Erreur lors de la génération des recommandations IA: {ai_error}").dict()
        
        # Préparer les résultats
        results = {
            'ai_analysis': {
                'status': 'completed',
                'message': 'Analyse IA terminée avec succès',
                'dataset_id': dataset_id,
                'audit_report_id': latest_audit.id,
                'recommendations_count': len(ai_recommendations),
                'recommendations': ai_recommendations
            }
        }
        
        logger.info(f"Analyse IA terminée avec succès pour: {dataset.link}")
        return TaskResult(error=False, results=results, message='Analyse IA terminée avec succès').dict()
        
    except DataSet.DoesNotExist:
        logger.error(f"Dataset non trouvé avec l'ID: {dataset_id}")
        return TaskResult(error=True, message=f"Dataset non trouvé avec l'ID: {dataset_id}").dict()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse IA du dataset {dataset_id}: {e}")
        return TaskResult(error=True, message=f"Erreur lors de l'analyse IA du dataset {dataset_id}: {e}").dict()


@dramatiq.actor(queue_name="upload",
                max_retries=0,
                actor_name="ml_app.upload_dataset_task",
                min_backoff=1000, 
                time_limit=60000*10,  # 10 minutes timeout
                store_results=True)
def upload_dataset_task(dataset_id: int):
    """
    Upload a dataset to the S3 bucket.
    """
    logger.info(f"Début de l'upload du dataset: {dataset_id}")
    try:
        dataset = DataSet.objects.get(id=dataset_id)
        
        # Vérifier si le bucket est configuré
        if not dataset.bucket:
            logger.error(f"Aucun bucket configuré pour le dataset {dataset.name}")
            return TaskResult(error=True, message=f"Aucun bucket configuré pour le dataset {dataset.name}").dict()
        
        # Vérifier si le dataset est déjà téléchargé
        if dataset.downloaded:
            logger.info(f"Dataset {dataset.name} déjà présent dans le bucket S3")
            return TaskResult(error=False, message=f"Dataset {dataset.name} déjà présent dans le bucket S3", already_exists=True).dict()
        
        # Effectuer l'upload
        logger.info(f"Upload du dataset {dataset.name} vers S3...")
        success = dataset.upload_dataset()
        
        if success:
            logger.info(f"Upload terminé avec succès pour le dataset {dataset.name}")
            return TaskResult(
                error=False,
                message=f"Dataset {dataset.name} téléchargé et uploadé avec succès vers S3",
                dataset_id=dataset_id,
                dataset_name=dataset.name,
                bucket_name=dataset.bucket.bucket_name
            ).dict()
        else:
            logger.error(f"Échec de l'upload du dataset {dataset.name}")
            return TaskResult(error=True, message=f"Erreur lors du téléchargement/upload du dataset {dataset.name}").dict()
            
    except DataSet.DoesNotExist:
        logger.error(f"Dataset non trouvé avec l'ID: {dataset_id}")
        return TaskResult(error=True, message=f"Dataset non trouvé avec l'ID: {dataset_id}").dict()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du dataset {dataset_id}: {e}")
        return TaskResult(error=True, message=f"Erreur lors de l'upload du dataset: {str(e)}").dict()


@dramatiq.actor(queue_name="mlflow_template",
                max_retries=0,
                actor_name="ml_app.generate_mlflow_template_task",
                min_backoff=1000,
                time_limit=60000*5,
                store_results=True)
def generate_mlflow_template_task(recommendation_id: int, model_type: str, dataset_id: int):
    """
    Génère un template MLflow adapté au type de modèle via LLM et le sauvegarde.
    """
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    from django_app_ml.models import IARecommandation, DataSet
    from django.conf import settings
    import os

    logger.info(f"Génération du template MLflow pour model_type={model_type}, recommendation_id={recommendation_id}, dataset_id={dataset_id}")
    try:
        # Récupérer la recommandation et le dataset
        recommendation = IARecommandation.objects.get(id=recommendation_id)
        dataset = DataSet.objects.get(id=dataset_id)

        # Lire le template de base
        template_path = os.path.join(settings.BASE_DIR, "django-app-ml/django_app_ml/templates/mlflow/train_template.py.j2")
        with open(template_path, "r") as f:
            base_template = f.read()

        # Préparer le prompt
        system_prompt = (
            "Tu es un expert MLflow et Python. "
            "Adapte le template suivant pour entraîner un modèle de type : {model_type}. "
            "Le code doit être prêt à l'emploi pour ce type de modèle, avec les bonnes librairies, preprocessing, et logique d'entraînement. "
            "Garde le style du template de base. "
            "Type de modèle demandé : {model_type}."
        ).format(model_type=model_type)

        user_prompt = (
            "Voici le template de base à adapter :\n\n" + base_template + "\n\n"
            "Le dataset s'appelle : {dataset_name}. "
            "Adapte le code pour le modèle : {model_type}. "
            "Ne réponds qu'avec le code Python complet."
        ).format(dataset_name=dataset.name, model_type=model_type)

        # Appel LLM
        llm = ChatOpenAI(model=getattr(settings, "OPENAI_MODEL", "gpt-4"), temperature=0.2, api_key=settings.OPENAI_API_KEY)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        generated_code = response.content.strip()

        # Sauvegarde dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp_file:
            tmp_file.write(generated_code)
            tmp_file_path = tmp_file.name

        # Création de l'objet MLFlowTemplate
        with open(tmp_file_path, "rb") as f:
            template_obj = MLFlowTemplate.objects.create(
                name=f"{model_type} - {dataset.name}",
                description=f"Template MLflow généré pour {model_type}",
                model_type=model_type,
                recommendation=recommendation,
            )
            template_obj.file.save(f"mlflow_template_{model_type}_{dataset.id}.py", f)
            template_obj.save()

        os.remove(tmp_file_path)
        logger.info(f"Template MLflow généré et sauvegardé (id={template_obj.id})")
        return {"template_id": template_obj.id}

    except Exception as e:
        logger.error(f"Erreur lors de la génération du template MLflow : {e}")
        return {"error": str(e)}
