"""
Views for the Django ML Application

This module contains all the views for the machine learning scoring application,
including data visualization, model training, prediction, and task management.
"""

import base64
import io
import zipfile
from itertools import chain
import pandas as pd
from matplotlib import pyplot as plt
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import requests
import tempfile
import os
from pathlib import Path

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    JsonResponse,
    StreamingHttpResponse,
)
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, CreateView, DetailView
from django.urls import reverse_lazy
from django_dramatiq.models import Task
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.custom import ShiftTemplateView
from core.settings import MODEL_PATH
from home.models import Project

from .mixins import ParquetQuerySetMixin, TaskViewMixin
from .models import DataSet, IAModel, ParquetBase, Bucket, MLFlowTemplate, IARecommandation
from .renderer import CustomScoringAppTemplateRenderer
from .serializer import (
    DatasetSerializer,
    IAModelSerializer,
    TaskSerializer,
    BucketSerializer,
)
from .task_utils import TaskResultManager
from .tasks import predict_task, train_task, audit_dataset_task, analyse_ia_task, upload_dataset_task, generate_mlflow_template_task
from .forms import DatasetForm, ModelIAForm
from .logging import get_logger
from .exceptions import (
    AuditDatasetException,
    DatasetNotFoundError,
    DatasetAccessError,
    DatasetValidationError,
)
from .schema.task import TaskResult

# Configure logger for this module
logger = get_logger(__name__)


class ScoringAppBaseView(GenericAPIView):
    """
    Base view class for scoring application views.

    Provides custom renderer classes to format JSON results on template views.
    CustomScoringAppTemplateRenderer allows overriding default REST framework templates
    while keeping BrowserAPI view functionality without declaring a default class in settings.
    """

    renderer_classes = [CustomScoringAppTemplateRenderer, JSONRenderer]


@method_decorator(cache_page(60 * 10), name="dispatch")  # Cache for 10 minutes
class DatasetAnalysisView(TemplateView, ParquetQuerySetMixin):
    """
    View for data visualization with plots and tables.

    TODO:
    - Modify storage to use ClickHouse
    - Currently uses Parquet files for data storage
    """

    template_name = "scoring_app/data_visualisation.html"
    queryset = DataSet.objects.all()
    serializer_class = DatasetSerializer

    def base64_encode(self, plot: plt.Figure) -> str:
        """
        Convert matplotlib figure to base64 encoded string.

        Args:
            plot: Matplotlib figure to encode

        Returns:
            Base64 encoded string representation of the plot
        """
        buffer = io.BytesIO()
        plot.savefig(buffer, format="png")
        buffer.seek(0)
        b64code = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()
        return b64code

    def get_context_data(self, **kwargs):
        """
        Add notebook URL to context for data visualization.

        Returns:
            Context dictionary with notebook URL
        """
        context = super().get_context_data()
        context["notebook"] = Project.objects.get(title="Model de scoring").notebook.url
        return context


class PredictView(ScoringAppBaseView):
    """
    View to test the prediction of a model after deployment.
    """

    serializer_class = IAModelSerializer

    def get_serializer(self, *args, **kwargs):
        """
        Get serializer with default values for form pre-filling.

        Returns:
            Configured serializer instance
        """
        if self.request.method == "POST":
            kwargs.setdefault("instance", IAModel.objects.first())
        return super().get_serializer(*args, **kwargs)

    def get(self, request):
        """
        Handle GET requests for prediction form.

        Returns:
            Empty response for form display
        """
        return Response(data={})

    def post(self, request):
        """
        Launch a prediction task for a new client.

        Returns:
            JSON response with task ID and status, or error details
        """
        if not self.request.data:
            serializer = self.get_serializer()
        else:
            serializer = self.get_serializer(data=self.request.data)

        if serializer.is_valid():
            logger.info(f"Predict client: {serializer.validated_data}")
            task = predict_task.send_with_options(
                kwargs={
                    "checkpoint": TrainView.checkpoint,
                    "client": serializer.validated_data,
                }
            )
            return Response(
                data={
                    "message_id": task.message_id,
                    "status": "pending",
                }
            )
        else:
            return Response(data={"error": serializer.errors})


class MainAppView(ShiftTemplateView):
    """
    Main application view for the ml app.
    Serves the main dashboard interface.
    """

    template_name = "django_app_ml/main.html"
    js_file = "django-app-ml/static/ml_app/js/main.js"

    def get_context_data(self, **kwargs):
        """
        Add datasets and models to context.
        """
        context = super().get_context_data(**kwargs)
        context["page_title"] = "ML Platform - plugin Django"
        context["datasets"] = DataSet.objects.all()
        context["models"] = IAModel.objects.all()
        context["buckets"] = Bucket.objects.all()
        return context


class ModelIACreateFormView(CreateView):
    """
    View for creating a new model.
    """

    template_name = "django_app_ml/modelia_create_form.html"
    form_class = ModelIAForm
    success_url = reverse_lazy("django_app_ml:main")

    def get_form_kwargs(self):
        """
        Return the keyword arguments for instantiating the form.
        Add the dataset id to the form instantiation to call the POST with the good dataset id
        Args:
            dataset_id: ID of the dataset

        Returns:
            Keyword arguments for the form
        """
        kwargs = super().get_form_kwargs()
        kwargs["dataset_id"] = self.kwargs.get("dataset_id")
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Add dataset to context to call the POST with the good dataset id
        """
        context = super().get_context_data(**kwargs)
        context["dataset_id"] = self.kwargs.get("dataset_id")
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        logger.debug(f"Form valid: {form.cleaned_data}")
        self.object = form.save()
        return super().form_valid(form)


class DatasetCreateFormView(CreateView):
    """
    View for creating a new dataset.
    """

    template_name = "django_app_ml/dataset_create_form.html"
    form_class = DatasetForm
    success_url = reverse_lazy("django_app_ml:main")


class MLFlowTemplateDownloadView(TaskViewMixin, APIView):
    """
    Vue pour générer ou télécharger un template MLflow personnalisé selon le type de modèle.
    POST : génère ou récupère le template (lance la tâche LLM si besoin)
    GET :
      - avec ?task_id=... : statut de génération
      - avec /<template_id>/ : téléchargement du template
    """
    queue_name = "mlflow_template"

    def post(self, request):
        dataset_id = request.data.get("dataset_id")
        recommendation_id = request.data.get("recommendation_id")
        model_type = request.data.get("model_type")
        if not (dataset_id and recommendation_id and model_type):
            return Response({"error": "dataset_id, recommendation_id et model_type sont requis"}, status=400)

        # Vérifier si un template existe déjà
        template_qs = MLFlowTemplate.objects.filter(
            recommendation_id=recommendation_id,
            model_type=model_type
        )
        if template_qs.exists():
            template = template_qs.first()
            return Response({
                "status": "ready",
                "template_id": template.id,
                "download_url": reverse("django_app_ml:mlflow-template-download", args=[template.id])
            })

        # Sinon, lancer la tâche via launch_task du mixin
        return self.launch_task(
            task_func=generate_mlflow_template_task,
            task_kwargs={
                "recommendation_id": recommendation_id,
                "model_type": model_type,
                "dataset_id": dataset_id
            },
            success_message="Génération du template MLflow lancée",
            error_message="Erreur lors du lancement de la génération du template MLflow"
        )

    def get(self, request, template_id=None):
        # Si ?task_id=... : polling du statut
        task_id = request.GET.get("task_id")
        if task_id:
            return self.get_task_status(task_id, task_name="Génération du template MLflow")
        # Sinon, téléchargement du template généré
        if template_id is not None:
            try:
                template = MLFlowTemplate.objects.get(id=template_id)
                if not template.file:
                    return Response({"error": "Le template n'est pas encore prêt."}, status=404)
                response = HttpResponse(template.file, content_type="text/x-python")
                response["Content-Disposition"] = f"attachment; filename=mlflow_template_{template.model_type}_{template.id}.py"
                return response
            except MLFlowTemplate.DoesNotExist:
                return Response({"error": "Template MLflow introuvable."}, status=404)
        return Response({"error": "template_id requis pour le téléchargement."}, status=400)


class DatasetAnalysisDetailView(ShiftTemplateView):
    """
    View for analyzing a specific dataset.
    """

    template_name = "django_app_ml/dataset_analysis.html"
    js_file = "django-app-ml/static/js/dataset_analysis/main.js"

    def get_context_data(self, **kwargs):
        """
        Add dataset to context.
        """
        context = super().get_context_data(**kwargs)
        dataset_id = self.kwargs.get("dataset_id")
        try:
            context["dataset"] = DataSet.objects.get(id=dataset_id)
            context["models"] = IAModel.objects.filter(dataset=context["dataset"])
        except DataSet.DoesNotExist:
            context["dataset"] = None
            context["error"] = "Dataset non trouvé"
        return context


class ModelDetailView(DetailView):
    """
    View for displaying details of a specific model.
    """

    model = IAModel
    template_name = "django_app_ml/model_detail.html"
    js_file = "django-app-ml/static/ml_app/js/model_detail.js"
    context_object_name = "model"

    def get_context_data(self, **kwargs):
        """
        Add model and related data to context.
        """
        context = super().get_context_data(**kwargs)
        context["model_metrics"] = {
            "accuracy": 0.85,  # Exemple de métrique
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "training_date": "2024-01-15",
            "last_updated": "2024-01-20",
            "version": "1.0.0",
        }
        return context


class UploadDatasetView(ScoringAppBaseView):
    """
    View for uploading dataset data to increase datasets.
    Handles CSV file uploads and bulk dataset data import.
    """

    serializer_class = DatasetSerializer

    def post(self, request, *args, **kwargs):
        """
        Process uploaded CSV file and import dataset data.

        Returns:
            JSON response with success message or error details
        """
        file_serializer = self.serializer_class(data=self.request.data)
        if file_serializer.is_valid():
            # Read CSV file
            df = pd.read_csv(file_serializer.validated_data["file"])

            # Convert to dataset records
            dataset_serializer = DatasetSerializer(
                data=df.to_dict(orient="records"), many=True
            )

            if dataset_serializer.is_valid():
                dataset_serializer.save()
                return Response(
                    {"message": "Import réussi ✅"}, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    dataset_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MarimoView(ShiftTemplateView):
    """
    View for notebook visualization.

    To use from the UI, convert Jupyter notebooks with Marimo and convert to HTML.
    This view only visualizes HTML files - editing is not allowed.
    """

    template_name = "django_app_ml/notebook_viewer.html"

    def get(self, request, notebook):
        """
        Handle GET requests for notebook viewing.

        Args:
            notebook: Name of the notebook to display

        Returns:
            Rendered template with notebook URL
        """
        self.notebook = notebook
        return super().get(request)

    def get_context_data(self, **kwargs):
        """
        Add notebook URL to context.

        Returns:
            Context dictionary with notebook media URL
        """
        context = super().get_context_data(**kwargs)
        context["notebook"] = settings.MEDIA_URL + f"notebooks/{self.notebook}"
        return context


######### REST API #########


class BucketModelViewSet(ModelViewSet):
    """
    Viewer for buckets.
    """

    model = Bucket
    queryset = Bucket.objects.all()
    serializer_class = BucketSerializer
    lookup_field = "id"


class TaskViewSet(ReadOnlyModelViewSet):
    """
    Read-only viewset for task management.

    Provides read-only access to Dramatiq tasks with UUID-based lookup.
    """

    queryset = Task.tasks.all()
    serializer_class = TaskSerializer
    lookup_field = "id"
    lookup_value_regex = "[0-9a-f-]{36}"  # UUID pattern


@method_decorator(cache_page(60 * 10), name="dispatch")  # Cache for 10 minutes
class IAModelModelViewSet(ModelViewSet):
    """
    Viewer for IA models.
    """

    model = IAModel
    queryset = IAModel.objects.all()
    serializer_class = IAModelSerializer


class DatasetModelViewSet(ModelViewSet):
    """
    API view for getting dataset details.
    """

    queryset = DataSet.objects.all()
    serializer_class = DatasetSerializer
    lookup_field = "id"

    def get_queryset(self):
        """
        Get the queryset for the dataset detail view.
        """
        return DataSet.objects.all()


class DatasetDownloadView(APIView, TaskViewMixin):
    """
    API view for downloading dataset to S3 bucket or local ZIP file.
    """
    queue_name = "upload"

    def download_dataset_as_zip(self, dataset):
        """
        Download dataset from URL and create a ZIP file directly during streaming.
        
        Args:
            dataset: DataSet instance
            
        Returns:
            tuple: (success: bool, zip_content: bytes or None, filename: str or None, error: str or None)
        """
        try:
            # Download the file from URL
            response = requests.get(dataset.link, stream=True)
            response.raise_for_status()
            
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Stream the content directly to the ZIP
                file_content = b''
                for chunk in response.iter_content(chunk_size=8192):
                    file_content += chunk
                
                # Add the file to the ZIP
                zipf.writestr(f"{dataset.name}.zip", file_content)
            
            # Get the ZIP content
            zip_buffer.seek(0)
            zip_content = zip_buffer.getvalue()
            
            # Generate ZIP filename
            zip_filename = f"{dataset.name}_v{dataset.version}.zip"
            
            return True, zip_content, zip_filename, None
                
        except requests.RequestException as e:
            logger.error(f"Error downloading dataset from {dataset.link}: {e}")
            return False, None, None, f"Erreur lors du téléchargement: {str(e)}"
        except Exception as e:
            logger.error(f"Error creating ZIP file for dataset {dataset.name}: {e}")
            return False, None, None, f"Erreur lors de la création du ZIP: {str(e)}"

    def get(self, request, dataset_id):
        """
        Download dataset from URL to S3 bucket or as local ZIP file.

        Args:
            dataset_id: ID of the dataset

        Returns:
            JSON response indicating success or failure, or ZIP file download
        """
        # Check if this is a status check request
        task_id = request.GET.get("task_id")
        if task_id:
            return self.get_task_status(task_id, "Upload de dataset")
        
        try:
            dataset = DataSet.objects.get(id=dataset_id)
            # Check if dataset has a bucket configured
            if dataset.bucket:
                # Check if dataset already exists in S3
                if dataset.downloaded:
                    return Response(
                        {"message": "Dataset déjà présent dans le bucket S3", "status": "already_exists"},
                        status=status.HTTP_200_OK
                    )
                
                # Launch upload task instead of direct upload
                return self.launch_task(
                    task_func=upload_dataset_task,
                    task_kwargs={"dataset_id": dataset_id},
                    success_message="Tâche d'upload lancée avec succès",
                    error_message="Erreur lors du lancement de la tâche d'upload"
                )
            else:
                # No bucket configured, download as ZIP file
                success, zip_content, filename, error = self.download_dataset_as_zip(dataset)
                
                if success:
                    # Return ZIP file as download
                    response = HttpResponse(zip_content, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
                else:
                    return Response(
                        {"error": error},  # error contains error message here
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
        except DataSet.DoesNotExist:
            return Response(
                {"error": "Dataset non trouvé"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error in dataset download: {e}")
            return Response(
                {"error": f"Erreur inattendue: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestBucketConnectionView(APIView):
    """
    View for testing S3 bucket connection.
    """

    def get(self, request, bucket_id):
        """
        Test the S3 bucket connection for a specific bucket.

        Args:
            bucket_id: ID of the bucket to test

        Returns:
            JSON response indicating success or failure.
        """
        try:
            bucket = Bucket.objects.get(id=bucket_id)

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=bucket.access_key,
                aws_secret_access_key=bucket.secret_key,
                region_name=bucket.region,
                endpoint_url=bucket.endpoint,
            )

            # Try to list objects in the specific bucket to confirm connection
            s3_client.list_objects_v2(Bucket=bucket.bucket_name, MaxKeys=1)

            return Response(data={"success": True, "message": "Connexion réussie"})

        except Bucket.DoesNotExist:
            return Response(
                data={"success": False, "message": "Bucket non trouvé"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3 bucket connection failed for bucket {bucket_id}: {e}")
            return Response(
                data={"success": False, "message": f"Échec de la connexion: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except Exception as e:
            logger.error(f"Unexpected error testing bucket connection: {e}")
            return Response(
                data={"success": False, "message": f"Erreur inattendue: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AuditDatasetView(APIView, TaskViewMixin):
    """
    API view for auditing a dataset.
    """

    def post(self, request, dataset_id):
        """
        Launch an audit task for a dataset.
        """
        try:
            return self.launch_task(
                task_func=audit_dataset_task,
                task_kwargs={
                    "dataset_id": dataset_id,
                    "save_report": False,
                },
                success_message="Audit lancé avec succès",
                error_message="Erreur lors du lancement de l'audit"
            )
        except DataSet.DoesNotExist:
            return self._format_task_response(
                status="failed",
                message="Dataset non trouvé",
                task_id=None,
                error="Dataset non trouvé",
                http_status=status.HTTP_404_NOT_FOUND,
            )

    def get_audit_status(self, task_id):
        """
        Get the status of an audit task.
        """
        return self.get_task_status(task_id, "Audit")

    def get(self, request, dataset_id):
        """
        Get the status of an audit task.
        Returns different JSON responses based on task status:
        - pending: Task is waiting to be processed
        - running: Task is currently executing
        - completed: Task finished successfully with results
        - failed: Task failed with error details
        """
        if request.GET.get("task_id"):
            return self.get_audit_status(request.GET.get("task_id"))

        dataset = DataSet.objects.get(id=dataset_id)
        if dataset.reports.count() > 0:
            return self._format_task_response(
                status="completed",
                message="Audit terminé avec succès",
                task_id=None,
                result=TaskResult(error=False, results=dataset.reports.first().report, message="Audit terminé avec succès").dict(),
            )
        else:
            return self._format_task_response(
                status="unknown", message="Audit non terminé", task_id=None, result=None
            )


class AnalyseIAView(APIView, TaskViewMixin):
    """
    API view for AI analysis of a dataset.
    """

    def post(self, request, dataset_id):
        """
        Launch an AI analysis task for a dataset.
        """
        try:
            return self.launch_task(
                task_func=analyse_ia_task,
                task_kwargs={
                    "dataset_id": dataset_id,
                },
                success_message="Analyse IA lancée avec succès",
                error_message="Erreur lors du lancement de l'analyse IA"
            )
        except DataSet.DoesNotExist:
            return self._format_task_response(
                status="failed",
                message="Dataset non trouvé",
                task_id=None,
                error="Dataset non trouvé",
                http_status=status.HTTP_404_NOT_FOUND,
            )

    def get_ia_analysis_status(self, task_id):
        """
        Get the status of an AI analysis task.
        """
        return self.get_task_status(task_id, "Analyse IA")

    def get(self, request, dataset_id):
        """
        Get the status of an AI analysis task.
        Returns different JSON responses based on task status:
        - pending: Task is waiting to be processed
        - running: Task is currently executing
        - completed: Task finished successfully with results
        - failed: Task failed with error details
        """
        if request.GET.get("task_id"):
            return self.get_ia_analysis_status(request.GET.get("task_id"))

        dataset = DataSet.objects.get(id=dataset_id)
        if dataset.recommendations.count() > 0:
            return self._format_task_response(
                status="completed",
                message="Analyse IA terminée avec succès",
                task_id=None,
                result=TaskResult(error=False, results=dataset.recommendations.first().recommendation, message="Analyse IA terminée avec succès").dict(),
            )
        else:
            return self._format_task_response(
                status="unknown", message="Analyse IA non terminée", task_id=None, result=None
            )
