from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage
from django_app_ml.app_settings import app_settings


class ParquetBase(models.Model):
    file = models.FileField(upload_to="parquet")
    model_link = models.CharField(max_length=50)

    def __str__(self):
        return self.model_link + "-" + self.file.name
    
class Bucket(models.Model):
    endpoint = models.URLField(default="https://s3.eu-west-3.amazonaws.com")
    access_key = models.CharField(max_length=50)
    secret_key = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    bucket_name = models.CharField(max_length=50)

    def __str__(self):
        return self.bucket_name
    


class DataSet(models.Model):
    link = models.URLField()
    name = models.CharField(max_length=50)
    description = models.TextField()
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bucket = models.ForeignKey(Bucket, on_delete=models.CASCADE, related_name="datasets", null=True, blank=True)

    def __str__(self):
        return self.name


class IAModel(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    dataset = models.ForeignKey(
        DataSet, on_delete=models.CASCADE, related_name="iamodels"
    )

    def __str__(self):
        return f"{self.name} - {self.dataset.name}"


class MLFlowTemplate(models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(
        upload_to="mlflow",
        storage=app_settings.storage,
    )
    description = models.TextField()

    def __str__(self):
        return self.name
