import logging
import dramatiq
import pandas as pd
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from .logging import get_logger
from .ml import train, predict
from .dataset_audit import PandasDatasetAuditor
from .models import Bucket, AuditReport, DataSet, IARecommandation
from .exceptions import AuditDatasetException, DatasetNotFoundError, DatasetAccessError, DatasetValidationError
from .recommandation import get_ai_recommendations
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
                return {'error': True, **AuditDatasetException.exception_to_dict(exception)}
        else:
            bucket_obj = None
            
        auditor = PandasDatasetAuditor(bucket_obj)
        results = auditor.full_audit(dataset.link, save_report=save_report, report_path=report_path)
        AuditReport.objects.create(dataset=dataset, report=results)
        logger.info(f"Audit terminé avec succès pour: {dataset.link}")
        return {
            'error': False,
            'results': results,
            'message': 'Audit terminé avec succès'
        }
        
    except FileNotFoundError as e:
        logger.error(f"Fichier dataset non trouvé: {dataset.link}")
        exception = DatasetNotFoundError(f"Fichier dataset non trouvé: {dataset.link}")
        return {'error': True, **AuditDatasetException.exception_to_dict(exception)}
        
    except PermissionError as e:
        logger.error(f"Erreur de permission pour le dataset {dataset.link}: {e}")
        exception = DatasetAccessError(f"Erreur de permission pour le dataset {dataset.link}: {e}")
        return {'error': True, **AuditDatasetException.exception_to_dict(exception)}
        
    except ValueError as e:
        logger.error(f"Erreur de validation du dataset {dataset.link}: {e}")
        exception = DatasetValidationError(f"Erreur de validation du dataset {dataset.link}: {e}")
        return {'error': True, **AuditDatasetException.exception_to_dict(exception)}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'audit du dataset {dataset.link}: {e}")
        exception = AuditDatasetException(f"Erreur lors de l'audit du dataset {dataset.link}: {e}")
        return {'error': True, **AuditDatasetException.exception_to_dict(exception)}


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
            return {
                'error': True,
                'message': f"Aucun rapport d'audit trouvé pour le dataset {dataset_id}. Veuillez d'abord effectuer un audit."
            }
        
        # Générer les recommandations IA
        logger.info(f"Génération des recommandations IA pour le dataset {dataset_id}")
        try:
            ai_recommendations = get_ai_recommendations(audit_report)
            logger.info(f"Génération réussie de {len(ai_recommendations)} recommandations IA")
            IARecommandation.objects.create(dataset=dataset, recommendation=ai_recommendations)
        except Exception as ai_error:
            logger.error(f"Erreur lors de la génération des recommandations IA: {ai_error}")
            return {
                'error': True,
                'message': f"Erreur lors de la génération des recommandations IA: {ai_error}"
            }
        
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
        return {
            'error': False,
            'results': results,
            'message': 'Analyse IA terminée avec succès'
        }
        
    except DataSet.DoesNotExist:
        logger.error(f"Dataset non trouvé avec l'ID: {dataset_id}")
        return {
            'error': True,
            'message': f"Dataset non trouvé avec l'ID: {dataset_id}"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse IA du dataset {dataset_id}: {e}")
        return {
            'error': True,
            'message': f"Erreur lors de l'analyse IA du dataset {dataset_id}: {e}"
        }



