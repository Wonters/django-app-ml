from django.apps import AppConfig
from django_app_ml.app_settings import app_settings
from django_app_ml.logging import get_logger

logger = get_logger(__name__)

class MlAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_app_ml'

    def ready(self):
        """
        Set the default media storage to the app_settings.storage
        """
        from django.conf import settings
        settings.DEFAULT_MEDIA_STORAGE = app_settings.storage
        if settings.INSTALLED_APPS.count("django_app_ml") > 1 and settings.INSTALLED_APPS.count("storages") == 0:
            logger.warning("django_app_ml is installed without storages not installed")
            logger.info("Adding storages to INSTALLED_APPS")
            settings.INSTALLED_APPS.append("storages")

