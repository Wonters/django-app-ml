
from django.urls import path, include
from ..views import MarimoView, TaskViewSet
from rest_framework.routers import SimpleRouter, DefaultRouter

app_name="ml_app"

# Default router is used to handle uuid task in django dramatiq models
router = DefaultRouter()
router.register('tasks', TaskViewSet, basename="task")

urlpatterns = [
    path('scoring_model/',include('ml_app.urls.urls_scoring_app', namespace='scoring_app')),
    path('notebooks/<str:notebook>', MarimoView.as_view(), name='marimo-view'),
    path("api/", include(router.urls))
]