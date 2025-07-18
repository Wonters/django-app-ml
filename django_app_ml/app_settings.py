
class AppSettings:
    def __init__(self, prefix):
        self.prefix = prefix

    def _setting(self, name, dflt):
        """
        Get a setting from django.conf.settings, falling back to the default.
        If the default is not given, uses the setting from django.conf.global_settings.
        """
        from django.conf import settings
        return getattr(settings, self.prefix + name, dflt)
    
    @property
    def mlflow_bucket_name(self):
        return self._setting('APP_ML_MLFLOW_BUCKET_NAME', 'mlflow')
    
    @property
    def mlflow_bucket_region(self):
        return self._setting('APP_ML_MLFLOW_BUCKET_REGION', 'us-east-1')
    
    @property
    def mlflow_bucket_access_key(self):
        return self._setting('APP_ML_MLFLOW_BUCKET_ACCESS_KEY', 'mlflow')
    
    @property
    def mlflow_bucket_secret_key(self):
        return self._setting('APP_ML_MLFLOW_BUCKET_SECRET_KEY', 'mlflow')
    
    @property
    def storage_class(self):
        return self._setting('APP_ML_STORAGE_CLASS', 'storages.backends.s3boto3.S3Boto3Storage')
    
    @property
    def storage(self):
        from storages.backends.s3boto3 import S3Boto3Storage
        from django.core.files.storage import FileSystemStorage
        return S3Boto3Storage(
            bucket_name=self.mlflow_bucket_name,
            region_name=self.mlflow_bucket_region,
            access_key=self.mlflow_bucket_access_key,
            secret_key=self.mlflow_bucket_secret_key,
        ) if self.storage_class == 'storages.backends.s3boto3.S3Boto3Storage' else FileSystemStorage()
    
    # Template configuration
    @property
    def templates_dir(self):
        """Base templates directory for django-app-ml"""
        from django.conf import settings
        from pathlib import Path
        return self._setting('APP_ML_TEMPLATES_DIR', 
                           Path(settings.BASE_DIR) / "django-app-ml/django_app_ml/templates")
    
    
    @property
    def template_dirs(self):
        """List of all template directories for django-app-ml"""
        return [
            self.templates_dir,
        ]
    
    @property
    def base_template_name(self):
        """Base template name for django-app-ml"""
        return self._setting('APP_ML_BASE_TEMPLATE_NAME', 'django_app_ml/base.html')
    
    @property
    def main_template_name(self):
        """Main template name for django-app-ml"""
        return self._setting('APP_ML_MAIN_TEMPLATE_NAME', 'django_app_ml/main.html')
    
    @property
    def model_detail_template_name(self):
        """Model detail template name"""
        return self._setting('APP_ML_MODEL_DETAIL_TEMPLATE_NAME', 'django_app_ml/model_detail.html')
    
    @property
    def dataset_analysis_template_name(self):
        """Dataset analysis template name"""
        return self._setting('APP_ML_DATASET_ANALYSIS_TEMPLATE_NAME', 'django_app_ml/dataset_analysis.html')
    
    @property
    def train_template_name(self):
        """Training template name"""
        return self._setting('APP_ML_TRAIN_TEMPLATE_NAME', 'django_app_ml/train.html')
    
    @property
    def data_visualisation_template_name(self):
        """Data visualization template name"""
        return self._setting('APP_ML_DATA_VISUALISATION_TEMPLATE_NAME', 'django_app_ml/data_visualisation.html')
    
    @property
    def notebook_viewer_template_name(self):
        """Notebook viewer template name"""
        return self._setting('APP_ML_NOTEBOOK_VIEWER_TEMPLATE_NAME', 'django_app_ml/notebook_viewer.html')
    
    @property
    def mlflow_train_template_name(self):
        """MLflow training template name"""
        return self._setting('APP_ML_MLFLOW_TRAIN_TEMPLATE_NAME', 'train_template.py.j2')

app_settings = AppSettings('APP_ML')