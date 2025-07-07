import base64
import io
import logging
from matplotlib import pyplot as plt
import pandas as pd
import httpx
from itertools import chain
from django.http import HttpResponse, HttpResponseNotAllowed, StreamingHttpResponse, JsonResponse
from django.views import View
from django.views.generic import TemplateView
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from django.urls import reverse
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django_dramatiq.models import Task
from core.settings import MODEL_PATH
from home.models import Project
from core.custom import ShiftTemplateView
from .models import Client, ParquetBase
from .serializer import ClientSerializer, ClientUploadSerializer, TaskSerializer, ClientPredictSerializer
from .tasks import train_task, predict_task
from .stream import MarimoStream
from .renderer import CustomScoringAppTemplateRenderer
from .mixins import ParquetQuerySetMixin

logger = logging.getLogger('scoring_model')

class ScoringAppBaseView(GenericAPIView):
    # Add JSONRenderer to format json results on template view
    # CustomScoringAppTemplateRenderer allow override default rest framework template
    # keeping BrowserAPI view and do not declare a default class in settings
    renderer_classes = [CustomScoringAppTemplateRenderer, JSONRenderer]



@method_decorator(cache_page(60 * 10), name='dispatch')  # 10 minutes
class ClientView(ModelViewSet, ScoringAppBaseView):
    """
    Dataset viewer
    """
    model = Client
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

@method_decorator(cache_page(60 * 10), name='dispatch')
class DataVisualisationView(TemplateView, ParquetQuerySetMixin):
    """
    View to visualize data
    Plot graphs and tables
    #todo: modify the storage to use clickhouse
    #todo: for the moment use parquet to store data
    """
    template_name = "scoring_app/data_visualisation.html"
    queryset = Client.objects.all()
    serializer_class=ClientSerializer

    def base64_encode(self, plot: plt.Figure):
        """

        :param plot:
        :return:
        """
        buffer = io.BytesIO()
        plot.savefig(buffer, format="png")
        buffer.seek(0)
        b64code = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        return b64code

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        context = super().get_context_data()
        context['notebook'] = Project.objects.get(title="Model de scoring").notebook.url
        return context

class TrainView(ShiftTemplateView, ParquetQuerySetMixin):
    """
    Launch a prediction of lown target from a new client
    """
    template_name = "scoring_app/train.html"
    queryset = ParquetBase.objects.get(model_link="Client")
    serializer_class = ClientSerializer
    js_file = "ml_app/static/ml_app/js/train.js"
    checkpoint = str(MODEL_PATH / "xgboost_checkpoint.model")

    def post(self, request):
        """"""
        logger.info(f"Train dataset: {self.queryset.file.path}")
        task = train_task.send_with_options(
            kwargs={'dataset_path':self.queryset.file.path,
                    'checkpoint':self.checkpoint},
            #on_failure=on_failure_callback
            )
        return JsonResponse(data={'message': "train running",
                                  "url": reverse('ml_app:task-detail',
                                                 kwargs={'id': task.message_id})})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.tasks.filter(queue_name='train', status__in=[Task.STATUS_ENQUEUED,
                                                                             Task.STATUS_RUNNING])
        return context
class PredictView(ScoringAppBaseView):
    """
    Launch a prediction of loan target from a new client
    """
    serializer_class = ClientPredictSerializer
    def get_serializer(self, *args, **kwargs):
        # Valeurs par défaut pour préremplir le formulaire
        if self.request.method == 'POST':
            kwargs.setdefault('instance', Client.objects.first())
        return super().get_serializer(*args, **kwargs)

    def get(self, request):
        return Response(data={})

    def post(self, request):
        if not self.request.data:
            serializer = self.get_serializer()
        else:
            serializer = self.get_serializer(data=self.request.data)
        if serializer.is_valid():
            """"""
            logger.info(f"Predict client: {serializer.validated_data}")
            task =predict_task.send_with_options(kwargs={'checkpoint': TrainView.checkpoint ,
                                                   'client': serializer.validated_data})
            return Response(data={
            'message_id': task.message_id,
            'status': '',
        })
        else:
            return Response(data={'error': serializer.errors})


class MainAppView(ShiftTemplateView):
    template_name = "scoring_app/main.html"
    js_file = "ml_app/static/ml_app/js/main.js"

class UploadClientView(ScoringAppBaseView):
    """
    Upload client data to increase datasets
    """
    serializer_class = ClientUploadSerializer
    def post(self, request,  *args, **kwargs):
        file_serializer = self.serializer_class(data=self.request.data)
        if file_serializer.is_valid():
            df = pd.read_csv(file_serializer.validated_data['file'])
            client_serializer = ClientSerializer(data=df.to_dict(orient="records"), many=True)
            if client_serializer.is_valid():
                client_serializer.save()
                return Response({'message': 'Import réussi ✅'}, status=status.HTTP_201_CREATED)
            else:
                return Response(client_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MarimoView(ShiftTemplateView):
    """
    Visualise notebook
    To use it from the ui, convert the jupiter notebook with marimo and convert it in html
    The view only visualise html files
    The edition is not allowed
    """
    template_name = "ml_app/notebook_viewer.html"

    def get(self, request, notebook):
        self.notebook = notebook
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notebook"] = settings.MEDIA_URL +f"notebooks/{self.notebook}"
        return context

class MarimoProxyView(View):
    """
    Notebook visualisation
    #todo: doesn't work and marimo can't serve multiple files, not the good way
    """

    def dispatch(self, request, path="", *args, **kwargs):
        marimo_url = f"http://{settings.MARIMO_HOST}/{path}"

        # Méthodes autorisées
        if request.method not in ['GET', 'POST', 'HEAD']:
            return HttpResponseNotAllowed(['GET', 'POST', 'HEAD'])

        # Préparation de la requête vers Marimo
        try:
            stream = MarimoStream(request, marimo_url)
            iterator = iter(stream)
            first_chunk = next(iterator)
            proxy_response = StreamingHttpResponse(
                streaming_content=chain([first_chunk], iterator),
                status=stream.status_code,
                content_type=stream.headers.get('content-type', 'text/html')
            )
            for key, value in stream.headers.items():
                if key.lower() != stream.exclude_headers.union({'transfer-encoding',
                                                                "content-encoding",
                                                                "content-length"}):
                    proxy_response[key] = value
                    proxy_response['content-type'] = "text/html"

            return proxy_response

        except httpx.RequestError as e:
            raise e
            return HttpResponse(
                "Marimo server unreachable",
                        status=502
            )


class TaskViewSet(ReadOnlyModelViewSet):
    queryset = Task.tasks.all()
    serializer_class = TaskSerializer
    lookup_field = "id"
    lookup_value_regex = '[0-9a-f-]{36}'