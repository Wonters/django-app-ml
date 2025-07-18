"""
Views for the Django ML Application

This module contains all the views for the machine learning scoring application,
including data visualization, model training, prediction, and task management.
"""

import base64
import io
from itertools import chain
import pandas as pd
from matplotlib import pyplot as plt
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, StreamingHttpResponse
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

from .mixins import ParquetQuerySetMixin
from .models import DataSet, IAModel, ParquetBase, Bucket
from .renderer import CustomScoringAppTemplateRenderer
from .serializer import (
    DatasetSerializer,
    IAModelSerializer,
    TaskSerializer,
    BucketSerializer,
)
from .tasks import predict_task, train_task, audit_dataset_task
from .forms import DatasetForm, ModelIAForm
from .logging import get_logger

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


@method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
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
        b64code = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        return b64code

    def get_context_data(self, **kwargs):
        """
        Add notebook URL to context for data visualization.
        
        Returns:
            Context dictionary with notebook URL
        """
        context = super().get_context_data()
        context['notebook'] = Project.objects.get(title="Model de scoring").notebook.url
        return context


class TrainView(ShiftTemplateView, ParquetQuerySetMixin):
    """
    View for launching model training tasks.
    Handles training of scoring models using XGBoost with checkpoint functionality.
    """
    template_name = "scoring_app/train.html"
    queryset = ParquetBase.objects.all()
    serializer_class = DatasetSerializer
    js_file = "django-app-ml/static/ml_app/js/train.js"
    checkpoint = str(MODEL_PATH / "xgboost_checkpoint.model")

    def post(self, request):
        """
        Launch a training task for the scoring model.
        
        Returns:
            JSON response with task status and detail URL
        """
        logger.info(f"Train dataset: {self.queryset.file.path}")
        task = train_task.send_with_options(
            kwargs={
                'dataset_path': self.queryset.file.path,
                'checkpoint': self.checkpoint
            }
        )
        return JsonResponse(data={
            'message': "train running",
            "url": reverse('django_app_ml:task-detail', kwargs={'id': task.message_id})
        })

    def get_context_data(self, **kwargs):
        """
        Add active training tasks to context.
        
        Returns:
            Context dictionary with enqueued and running tasks
        """
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.tasks.filter(
            queue_name='train', 
            status__in=[Task.STATUS_ENQUEUED, Task.STATUS_RUNNING]
        )
        return context


class PredictView(ScoringAppBaseView):
    """
    View for launching loan prediction tasks.
    
    Handles prediction of loan targets for new clients using trained models.
    """
    serializer_class = IAModelSerializer

    def get_serializer(self, *args, **kwargs):
        """
        Get serializer with default values for form pre-filling.
        
        Returns:
            Configured serializer instance
        """
        if self.request.method == 'POST':
            kwargs.setdefault('instance', IAModel.objects.first())
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
                    'checkpoint': TrainView.checkpoint,
                    'client': serializer.validated_data
                }
            )
            return Response(data={
                'message_id': task.message_id,
                'status': 'pending',
            })
        else:
            return Response(data={'error': serializer.errors})


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
        context['page_title'] = "ML Platform - plugin Django"
        context['datasets'] = DataSet.objects.all()
        context['models'] = IAModel.objects.all()
        return context
    
class ModelIACreateFormView(CreateView):
    """
    View for creating a new model.
    """
    template_name = "django_app_ml/modelia_create_form.html"
    form_class = ModelIAForm
    success_url = reverse_lazy('django_app_ml:main') 

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
        kwargs['dataset_id'] = self.kwargs.get('dataset_id')
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Add dataset to context to call the POST with the good dataset id 
        """
        context = super().get_context_data(**kwargs)
        context['dataset_id'] = self.kwargs.get('dataset_id')
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
    success_url = reverse_lazy('django_app_ml:main') 


class MLFlowTemplateDownloadView(APIView):
    """
    View for downloading the MLFlow template.
    """
    def generate_mlflow_script(self, dataset: DataSet):
        context = {
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "version": dataset.version,
                "path": dataset.bucket.endpoint,
                "target_column": 'none',
                "source": "s3"
            },
            "experiment_name": f"{dataset.name}_exp"
        }

        script_content = render_to_string("mlflow/train_template.py.j2", context)

        response = HttpResponse(script_content, content_type="text/x-python")
        response["Content-Disposition"] = f"attachment; filename=train_{dataset.name}.py"
        return response
    
    def get(self, request, dataset_id):
        self.object = DataSet.objects.get(id=dataset_id)
        logger.info(f"Generate MLFlow script for dataset {self.object.name} - {self.object.bucket}")
        return self.generate_mlflow_script(self.object)


class DatasetAnalysisDetailView(ShiftTemplateView):
    """
    View for analyzing a specific dataset.
    """
    template_name = "django_app_ml/dataset_analysis.html"
    js_file = "django-app-ml/static/js/dataset_analysis.js"

    def get_context_data(self, **kwargs):
        """
        Add dataset to context.
        """
        context = super().get_context_data(**kwargs)
        dataset_id = self.kwargs.get('dataset_id')
        try:
            context['dataset'] = DataSet.objects.get(id=dataset_id)
            context['models'] = IAModel.objects.filter(dataset=context['dataset'])
        except DataSet.DoesNotExist:
            context['dataset'] = None
            context['error'] = "Dataset non trouvé"
        return context


class ModelDetailView(DetailView):
    """
    View for displaying details of a specific model.
    """
    model = IAModel
    template_name = "django_app_ml/model_detail.html"
    js_file = "django-app-ml/static/ml_app/js/model_detail.js"
    context_object_name = 'model'

    def get_context_data(self, **kwargs):
        """
        Add model and related data to context.
        """
        context = super().get_context_data(**kwargs)
        context['model_metrics'] = {
            'accuracy': 0.85,  # Exemple de métrique
            'precision': 0.82,
            'recall': 0.88,
            'f1_score': 0.85,
            'training_date': '2024-01-15',
            'last_updated': '2024-01-20',
            'version': '1.0.0'
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
            df = pd.read_csv(file_serializer.validated_data['file'])
            
            # Convert to dataset records
            dataset_serializer = DatasetSerializer(
                data=df.to_dict(orient="records"), 
                many=True
            )
            
            if dataset_serializer.is_valid():
                dataset_serializer.save()
                return Response(
                    {'message': 'Import réussi ✅'}, 
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    dataset_serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            file_serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


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
    lookup_value_regex = '[0-9a-f-]{36}'  # UUID pattern


@method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
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


class DatasetDownloadView(APIView):
    """
    API view for downloading dataset data.
    """
    def get(self, request, dataset_id):
        """
        Download dataset data as CSV.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            CSV file response
        """
        try:
            dataset = DataSet.objects.get(id=dataset_id)
            
            # Ici vous pouvez ajouter la logique pour récupérer les données du dataset
            # Pour l'instant, on retourne un fichier CSV vide avec les métadonnées
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Dataset ID', 'Nom', 'Source', 'Status'])
            writer.writerow([
                dataset.id, 
                dataset.name, 
                dataset.source,
                "Déployé" if IAModel.objects.filter(dataset=dataset).exists() else "Non déployé"
            ])
            
            response = HttpResponse(
                output.getvalue(), 
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="dataset_{dataset_id}.csv"'
            
            return response
        except DataSet.DoesNotExist:
            return Response(
                {'error': 'Dataset non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
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
                's3',
                aws_access_key_id=bucket.access_key,
                aws_secret_access_key=bucket.secret_key,
                region_name=bucket.region,
                endpoint_url=bucket.endpoint
            )
            
            # Try to list objects in the specific bucket to confirm connection
            s3_client.list_objects_v2(Bucket=bucket.bucket_name, MaxKeys=1)
            
            return Response(data={
                "success": True,
                "message": "Connexion réussie"
            })
            
        except Bucket.DoesNotExist:
            return Response(data={
                "success": False,
                "message": "Bucket non trouvé"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3 bucket connection failed for bucket {bucket_id}: {e}")
            return Response(data={
                "success": False,
                "message": f"Échec de la connexion: {str(e)}"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Unexpected error testing bucket connection: {e}")
            return Response(data={
                "success": False,
                "message": f"Erreur inattendue: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AuditDatasetView(APIView):
    """
    API view for auditing a dataset.
    """
    def post(self, request, dataset_id):
        """
        Launch an audit task for a dataset.
        """
        try:
            dataset = DataSet.objects.get(id=dataset_id)
            task = audit_dataset_task.send_with_options(
                kwargs={    
                    'dataset_path': dataset.file.path,
                    'bucket': dataset.bucket.id if dataset.bucket else None
                }
            )
            return Response(data={
                'message_id': task.message_id,
                'status': 'pending',
                'message': 'Audit lancé avec succès'
            })
        except DataSet.DoesNotExist:
            return Response(
                {'error': 'Dataset non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'audit: {e}")
            return Response(
                {'error': f'Erreur lors du lancement de l\'audit: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, dataset_id):
        """
        Get the status of an audit task.
        """
        try:
            task_id = request.GET.get('task_id')
            if not task_id:
                return Response(
                    {'error': 'task_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer la tâche depuis Dramatiq
            task = Task.tasks.get(id=task_id)
            
            if task.status == Task.STATUS_DONE:
                # Tâche terminée, récupérer les résultats
                try:
                    result = task.result
                    return Response(data={
                        'status': 'completed',
                        'result': result,
                        'message': 'Audit terminé avec succès'
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des résultats: {e}")
                    return Response(data={
                        'status': 'error',
                        'error': 'Erreur lors de la récupération des résultats'
                    })
            elif task.status == Task.STATUS_FAILED:
                return Response(data={
                    'status': 'failed',
                    'error': 'L\'audit a échoué'
                })
            else:
                # Tâche en cours (enqueued, running, etc.)
                return Response(data={
                    'status': 'running',
                    'message': 'Audit en cours...'
                })
                
        except Task.DoesNotExist:
            return Response(
                {'error': 'Tâche non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return Response(
                {'error': f'Erreur lors de la récupération du statut: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )