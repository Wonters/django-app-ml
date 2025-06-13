from django.urls import path, include
from ..views import PredictView, UploadClientView, ClientView, DataVisualisationView, TrainView, MainAppView
from rest_framework.routers import SimpleRouter

app_name = "scoring_app"

# ViewSet only
router = SimpleRouter()
router.register("clients", ClientView, basename="clients")

urlpatterns = [
    path('', MainAppView.as_view(), name="main"),
    path('predict/', PredictView.as_view(), name="predict"),
    path("train/", TrainView.as_view(), name="train"),
    path("api/", include(router.urls)),
    path("upload/", UploadClientView.as_view(), name="upload"),
    path("visualisation/", DataVisualisationView.as_view(), name="visualise")
]