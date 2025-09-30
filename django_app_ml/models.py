from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage
from django_app_ml.app_settings import app_settings
from django_app_ml.validators import validate_url_or_s3
from pathlib import Path
from django.conf import settings
import requests
import io
import os
from django_dramatiq.models import Task
from concurrent.futures import ThreadPoolExecutor
from .logging import get_logger

logger = get_logger(__name__)

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
    
    def _extract_s3_key(self, link):
        """Extract the S3 key from a full S3 URL."""
        if link is not None and link.startswith('s3://'):
            # Remove s3:// prefix
            path_without_prefix = link[5:]
            # Split by first slash to separate bucket from key
            parts = path_without_prefix.split('/', 1)
            if len(parts) > 1:
                return parts[1]
            else:
                return ""
        else:
            # If it's not an S3 URL, use the link as is
            return link
    
    def check_if_file_exists(self, s3_key):
        from boto3 import client
        
        s3_client = client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint
        )
        try:
            s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File {s3_key} exists in bucket {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Error checking if file exists {s3_key}: {e}")
            return False
    
    @property
    def s3_client(self):
        """
        Return a S3 client
        """
        from boto3 import client
        return client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint
        )

    def upload_file(self, link):
        """
        Upload a file to the S3 bucket.
        """
        
        key = self._extract_s3_key(link)
        
        try:
            self.s3_client.upload_file(link, self.bucket_name, key)
            return True
        except Exception as e:
            logger.error(f"Error uploading file {link}: {e}")
            return False

    def download_file(self, link):
        """
        Download a file from the S3 bucket
        """
        
        key = self._extract_s3_key(link)
        
        try:
            file_path = Path(settings.MEDIA_ROOT) / f"datasets/{key}"
            self.s3_client.download_file(Bucket=self.bucket_name, Key=key, Filename=file_path)
            return True
        except Exception as e:
            logger.error(f"Error downloading file {link}: {e}")
            return False

    def upload_from_url(self, url, s3_key):
        """
        Download a file from a URL and upload it directly to S3 without local storage.
        
        Args:
            url: The URL to download the file from
            s3_key: The S3 key where to store the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Download the file from URL
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Upload directly to S3 using upload_fileobj
            self.s3_client.upload_fileobj(
                io.BytesIO(response.content),
                self.bucket_name,
                s3_key
            )
            
            logger.info(f"Successfully uploaded {url} to S3 as {s3_key}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False


class AuditReport(models.Model):
    dataset = models.ForeignKey("DataSet", on_delete=models.CASCADE, related_name="reports")
    report = models.JSONField(default=dict, null=True, blank=True)
    file = models.FileField(upload_to="reports", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dataset.name
    
class IARecommandation(models.Model):
    dataset = models.ForeignKey("DataSet", on_delete=models.CASCADE, related_name="recommendations")
    recommendation = models.JSONField(default=dict, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dataset.name

class DataSet(models.Model):
    link = models.URLField(validators=[validate_url_or_s3], null=True, blank=True, default='source du dataset')
    s3_key = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.TextField()
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bucket = models.ForeignKey(Bucket, on_delete=models.CASCADE, related_name="datasets", null=True, blank=True)

    def __str__(self):
        return self.name
    
    @property
    def downloaded(self):
        if self.bucket:
            return self.bucket.check_if_file_exists(self.s3_key)
        else:
            return False
        
    @property
    def last_download_task(self):
        task = Task.tasks.filter(queue_name="upload").first()
        if task and task.message.kwargs["dataset_id"] == self.id:
            return task
        return None

    def upload_dataset(self):
        """
        Upload a dataset to the S3 bucket.
        """
        if not self.bucket:
            logger.warning(f"No bucket configured for dataset {self.name}")
            return False
        
        # Check if it's a Kaggle dataset
        if 'kaggle' in self.link.lower():
            return self._upload_kaggle_dataset_sync()
        
        return self.bucket.upload_from_url(self.link, self.s3_key)
    
    @property
    def s3_location(self):
        """
        Return the S3 location of the dataset
        """
        return f"s3://{self.bucket.bucket_name}/{self.s3_key}"

    def _upload_kaggle_dataset_sync(self):
        """
        Synchronous wrapper for Kaggle dataset upload using ThreadPoolExecutor.
        """
        try:
            # Download Kaggle dataset to temporary directory
            downloaded_files = self.download_kaggle_dataset()
            
            if not downloaded_files:
                logger.error(f"Failed to download Kaggle dataset: {self.link}")
                return False
            
            # Use ThreadPoolExecutor for concurrent uploads
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Create upload tasks
                upload_futures = []
                for file_path in downloaded_files:
                    filename = os.path.basename(file_path)
                    s3_key = f"{self.name}/{filename}"
                    future = executor.submit(self._upload_file_to_s3_sync, file_path, s3_key)
                    upload_futures.append((future, file_path))
                
                # Wait for all uploads to complete and collect results
                success_count = 0
                for future, file_path in upload_futures:
                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                            logger.info(f"Successfully uploaded {os.path.basename(file_path)} to S3")
                        else:
                            logger.error(f"Failed to upload {os.path.basename(file_path)} to S3")
                    except Exception as e:
                        logger.error(f"Error uploading {os.path.basename(file_path)} to S3: {e}")
                    
                    # Clean up local file
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        logger.warning(f"Could not remove temporary file {file_path}: {e}")
            
            # Clean up the temporary directory
            temp_dir = os.path.dirname(downloaded_files[0]) if downloaded_files else None
            if temp_dir and os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    # Directory not empty, leave it for now
                    pass
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in _upload_kaggle_dataset_sync: {e}")
            return False

    def _upload_file_to_s3_sync(self, file_path, s3_key):
        """
        Synchronous method to upload a file to S3.
        """
        try:
            self.bucket.s3_client.upload_file(
                file_path,
                self.bucket.bucket_name,
                s3_key
            )
            return True
        except Exception as e:
            logger.error(f"Error uploading {file_path} to S3: {e}")
            raise e

    def download_dataset(self):
        """
        Download a dataset from the S3 bucket.
        """
        if self.bucket:
            return self.bucket.download_file(self.link)
        else:
            return None
        
    def download_kaggle_dataset(self):
        """
        Download a Kaggle dataset and return list of downloaded file paths.
        """
        try:
            from kaggle import KaggleApi
            import tempfile
            
            # Create temporary directory for download
            temp_dir = tempfile.mkdtemp()
            
            api = KaggleApi()
            api.authenticate()
            
            # Download dataset to temporary directory
            dataset_kaggle_name = self.link.replace("https://www.kaggle.com/datasets", "").lstrip("/")
            api.dataset_download_files(dataset_kaggle_name, path=temp_dir, unzip=True)
            
            # Get list of downloaded files
            downloaded_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    downloaded_files.append(file_path)
            
            logger.info(f"Downloaded {len(downloaded_files)} files from Kaggle dataset")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading Kaggle dataset {self.link}: {e}")
            return []


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
    # Ajout de la FK vers IARecommandation (nullable)
    recommendation = models.ForeignKey(
        IARecommandation, on_delete=models.SET_NULL, null=True, blank=True, related_name="mlflow_templates"
    )
    # Ajout du type de modèle (ex: RandomForest, CNN, etc)
    model_type = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name
