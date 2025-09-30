from django.urls import path, include
from ..views import (
    MarimoView,
    TaskViewSet,
    PredictView,
    DatasetDownloadView,
    DatasetModelViewSet,
    MainAppView,
    DatasetCreateFormView,
    DatasetAnalysisDetailView,
    MLFlowTemplateDownloadView,
    IAModelModelViewSet,
    ModelIACreateFormView,
    UploadDatasetView,
    ModelDetailView,
    BucketModelViewSet,
    TestBucketConnectionView,
    AuditDatasetView,
    AnalyseIAView,
)
from rest_framework.routers import SimpleRouter, DefaultRouter

app_name = "django_app_ml"

# Default router is used to handle uuid task in django dramatiq models
router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")
router.register("datasets", DatasetModelViewSet, basename="dataset")
router.register("models", IAModelModelViewSet, basename="model")
router.register("buckets", BucketModelViewSet, basename="bucket")

urlpatterns = [
    path("", MainAppView.as_view(), name="main"),
    path("notebooks/<str:notebook>", MarimoView.as_view(), name="marimo-view"),
    path("predict/", PredictView.as_view(), name="predict"),
    path("api/", include(router.urls)),
    path(
        "api/datasets/<int:dataset_id>/download/",
        DatasetDownloadView.as_view(),
        name="dataset-download",
    ),
    path("modelia/create/<int:dataset_id>/", ModelIACreateFormView.as_view(), name="modelia-create"),
    path("model/<int:pk>/detail/", ModelDetailView.as_view(), name="model-detail"),
    path("dataset/create/", DatasetCreateFormView.as_view(), name="dataset-create"),
    path(
        "dataset/<int:dataset_id>/analysis/",
        DatasetAnalysisDetailView.as_view(),
        name="dataset-analysis",
    ),

    path(
        "dataset/<int:dataset_id>/mlflow-template/",
        MLFlowTemplateDownloadView.as_view(),
        name="mlflow-template",
    ),
    path(
        "api/datasets/upload/",
        UploadDatasetView.as_view(),
        name="upload-dataset",
    ),
    path(
        "api/buckets/<int:bucket_id>/test-connection/",
        TestBucketConnectionView.as_view(),
        name="test-bucket-connection",
    ),
    path(
        "api/datasets/<int:dataset_id>/audit/",
        AuditDatasetView.as_view(),
        name="audit-dataset",
    ),
    path(
        "api/datasets/<int:dataset_id>/analyse-ia/",
        AnalyseIAView.as_view(),
        name="analyse-ia",
    ),
]
