from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django_dramatiq.models import Task
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from .models import DataSet, IAModel, ParquetBase, MLFlowTemplate
from .forms import DatasetForm, ModelIAForm
from .serializer import DatasetSerializer, IAModelSerializer, TaskSerializer


class BaseTestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test data
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
        
        self.model = IAModel.objects.create(
            name='Test Model',
            description='Test model description',
            dataset=self.dataset
        )


class MainAppViewTest(BaseTestCase):
    """Tests for MainAppView"""
    
    def test_main_app_view_get(self):
        """Test GET request to main app view"""
        url = reverse('django_app_ml:main')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app_ml/main.html')
        self.assertIn('datasets', response.context)
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], "ML Platform - plugin Django")


class DatasetAnalysisViewTest(BaseTestCase):
    """Tests for DatasetAnalysisView"""
    
    def test_dataset_analysis_view_get(self):
        """Test GET request to dataset analysis view"""
        url = reverse('django_app_ml:dataset-analysis', kwargs={'dataset_id': self.dataset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app_ml/dataset_analysis.html')
        self.assertIn('dataset', response.context)
        self.assertEqual(response.context['dataset'], self.dataset)
        self.assertIn('models', response.context)
    
    def test_dataset_analysis_view_invalid_dataset(self):
        """Test GET request with invalid dataset ID"""
        url = reverse('django_app_ml:dataset-analysis', kwargs={'dataset_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app_ml/dataset_analysis.html')
        self.assertIsNone(response.context['dataset'])
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], "Dataset non trouvé")


class TrainViewTest(BaseTestCase):
    """Tests for TrainView"""
    
    def setUp(self):
        super().setUp()
        # Create a test parquet file
        self.parquet_file = ParquetBase.objects.create(
            file=SimpleUploadedFile("test.parquet", b"test content"),
            model_link="test_model"
        )
    
    def test_train_view_get(self):
        """Test GET request to train view"""
        url = reverse('django_app_ml:train')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scoring_app/train.html')
        self.assertIn('tasks', response.context)
    
    @patch('django_app_ml.views.train_task')
    def test_train_view_post(self, mock_train_task):
        """Test POST request to train view"""
        mock_task = MagicMock()
        mock_task.message_id = 'test-message-id'
        mock_train_task.send_with_options.return_value = mock_task
        
        url = reverse('django_app_ml:train')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], "train running")
        self.assertIn('url', response_data)
        
        # Verify task was called
        mock_train_task.send_with_options.assert_called_once()


class PredictViewTest(BaseTestCase):
    """Tests for PredictView using APITestCase"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
        
        self.model = IAModel.objects.create(
            name='Test Model',
            description='Test model description',
            dataset=self.dataset
        )
    
    def test_predict_view_get(self):
        """Test GET request to predict view"""
        url = reverse('django_app_ml:predict')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {})
    
    @patch('django_app_ml.views.predict_task')
    def test_predict_view_post_valid_data(self, mock_predict_task):
        """Test POST request with valid data"""
        mock_task = MagicMock()
        mock_task.message_id = 'test-message-id'
        mock_predict_task.send_with_options.return_value = mock_task
        
        url = reverse('django_app_ml:predict')
        data = {
            'name': 'Test Prediction Model',
            'description': 'Test prediction description',
            'dataset': self.dataset.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message_id'], 'test-message-id')
        self.assertEqual(response.data['status'], 'pending')
        
        # Verify task was called
        mock_predict_task.send_with_options.assert_called_once()
    
    def test_predict_view_post_invalid_data(self):
        """Test POST request with invalid data"""
        url = reverse('django_app_ml:predict')
        data = {
            'name': '',  # Invalid: empty name
            'description': 'Test description',
            'dataset': 99999  # Invalid: non-existent dataset
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.data)
    
    def test_predict_view_post_empty_data(self):
        """Test POST request with empty data"""
        url = reverse('django_app_ml:predict')
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, 200)
        # Should return empty response when no data provided


class ModelICreateFormViewTest(BaseTestCase):
    """Tests for ModelICreateFormView"""
    
    def test_model_create_form_view_get(self):
        """Test GET request to model create form"""
        url = reverse('django_app_ml:modelia-create', kwargs={'dataset_id': self.dataset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app_ml/modelia_create_form.html')
        self.assertIn('form', response.context)
    
    def test_model_create_form_view_post_valid(self):
        """Test POST request with valid form data"""
        url = reverse('django_app_ml:modelia-create', kwargs={'dataset_id': self.dataset.id})
        data = {
            'name': 'New Test Model',
            'description': 'New test model description',
            'dataset': self.dataset.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(IAModel.objects.filter(name='New Test Model').exists())
    
    def test_model_create_form_view_post_invalid(self):
        """Test POST request with invalid form data"""
        url = reverse('django_app_ml:modelia-create', kwargs={'dataset_id': self.dataset.id})
        data = {
            'name': '',  # Invalid: empty name
            'description': 'Test description',
            'dataset': self.dataset.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)  # Stay on form page
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)


class DatasetCreateFormViewTest(BaseTestCase):
    """Tests for DatasetCreateFormView"""
    
    def test_dataset_create_form_view_get(self):
        """Test GET request to dataset create form"""
        url = reverse('django_app_ml:dataset-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app_ml/dataset_create_form.html')
        self.assertIn('form', response.context)
    
    def test_dataset_create_form_view_post_valid(self):
        """Test POST request with valid form data"""
        url = reverse('django_app_ml:dataset-create')
        data = {
            'name': 'New Test Dataset',
            'description': 'New test dataset description',
            'link': 'https://example.com/new-dataset'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(DataSet.objects.filter(name='New Test Dataset').exists())
    
    def test_dataset_create_form_view_post_invalid(self):
        """Test POST request with invalid form data"""
        url = reverse('django_app_ml:dataset-create')
        data = {
            'name': '',  # Invalid: empty name
            'description': 'Test description',
            'link': 'invalid-url'  # Invalid URL
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)  # Stay on form page
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)


class MLFlowTemplateDownloadViewTest(BaseTestCase):
    """Tests for MLFlowTemplateDownloadView"""
    
    def test_mlflow_template_download_view_get(self):
        """Test GET request to download MLFlow template"""
        url = reverse('django_app_ml:mlflow-template', kwargs={'dataset_id': self.dataset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/x-python')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'train_{self.dataset.name}.py', response['Content-Disposition'])
    
    def test_mlflow_template_download_view_invalid_dataset(self):
        """Test GET request with invalid dataset ID"""
        url = reverse('django_app_ml:mlflow-template', kwargs={'dataset_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class UploadDatasetViewTest(APITestCase):
    """Tests for UploadDatasetView"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_upload_dataset_view_post_valid_csv(self):
        """Test POST request with valid CSV file"""
        # Create a temporary CSV file
        csv_content = "name,description,link\nTest Dataset,Test Description,https://example.com"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        
        url = reverse('django_app_ml:upload-dataset')  # You'll need to add this URL
        data = {'file': csv_file}
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Import réussi ✅')
    
    def test_upload_dataset_view_post_invalid_file(self):
        """Test POST request with invalid file"""
        url = reverse('django_app_ml:upload-dataset')  # You'll need to add this URL
        data = {'file': 'not-a-file'}
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)


class MarimoViewTest(BaseTestCase):
    """Tests for MarimoView"""
    
    def test_marimo_view_get(self):
        """Test GET request to marimo view"""
        notebook_name = 'test_notebook.html'
        url = reverse('django_app_ml:marimo-view', kwargs={'notebook': notebook_name})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app_ml/notebook_viewer.html')
        self.assertIn('notebook', response.context)
        self.assertIn(notebook_name, response.context['notebook'])


class TaskViewSetTest(APITestCase):
    """Tests for TaskViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_task_list_view(self):
        """Test GET request to task list"""
        url = reverse('django_app_ml:task-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
    
    def test_task_detail_view(self):
        """Test GET request to task detail"""
        # Create a mock task
        task = Task.objects.create(
            actor_name='test_actor',
            queue_name='test_queue',
            status=Task.STATUS_ENQUEUED
        )
        
        url = reverse('django_app_ml:task-detail', kwargs={'id': task.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], str(task.id))


class IAModelModelViewSetTest(APITestCase):
    """Tests for IAModelModelViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
        
        self.model = IAModel.objects.create(
            name='Test Model',
            description='Test model description',
            dataset=self.dataset
        )
    
    def test_model_list_view(self):
        """Test GET request to model list"""
        url = reverse('django_app_ml:model-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Model')
    
    def test_model_detail_view(self):
        """Test GET request to model detail"""
        url = reverse('django_app_ml:model-detail', kwargs={'pk': self.model.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Test Model')
    
    def test_model_create_view(self):
        """Test POST request to create model"""
        url = reverse('django_app_ml:model-list')
        data = {
            'name': 'New Model',
            'description': 'New model description',
            'dataset': self.dataset.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'New Model')
    
    def test_model_update_view(self):
        """Test PUT request to update model"""
        url = reverse('django_app_ml:model-detail', kwargs={'pk': self.model.pk})
        data = {
            'name': 'Updated Model',
            'description': 'Updated description',
            'dataset': self.dataset.id
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Updated Model')
    
    def test_model_delete_view(self):
        """Test DELETE request to delete model"""
        url = reverse('django_app_ml:model-detail', kwargs={'pk': self.model.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 204)
        self.assertFalse(IAModel.objects.filter(pk=self.model.pk).exists())


class DatasetModelViewSetTest(APITestCase):
    """Tests for DatasetModelViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
    
    def test_dataset_list_view(self):
        """Test GET request to dataset list"""
        url = reverse('django_app_ml:dataset-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Dataset')
    
    def test_dataset_detail_view(self):
        """Test GET request to dataset detail"""
        url = reverse('django_app_ml:dataset-detail', kwargs={'pk': self.dataset.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Test Dataset')
    
    def test_dataset_create_view(self):
        """Test POST request to create dataset"""
        url = reverse('django_app_ml:dataset-list')
        data = {
            'name': 'New Dataset',
            'description': 'New dataset description',
            'link': 'https://example.com/new-dataset'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'New Dataset')
    
    def test_dataset_update_view(self):
        """Test PUT request to update dataset"""
        url = reverse('django_app_ml:dataset-detail', kwargs={'pk': self.dataset.pk})
        data = {
            'name': 'Updated Dataset',
            'description': 'Updated description',
            'link': 'https://example.com/updated-dataset'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Updated Dataset')
    
    def test_dataset_delete_view(self):
        """Test DELETE request to delete dataset"""
        url = reverse('django_app_ml:dataset-detail', kwargs={'pk': self.dataset.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 204)
        self.assertFalse(DataSet.objects.filter(pk=self.dataset.pk).exists())


class DatasetDownloadViewTest(APITestCase):
    """Tests for DatasetDownloadView"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
    
    def test_dataset_download_view_get(self):
        """Test GET request to download dataset"""
        url = reverse('django_app_ml:dataset-download', kwargs={'dataset_id': self.dataset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'dataset_{self.dataset.id}.csv', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Dataset ID', content)
        self.assertIn('Nom', content)
        self.assertIn('Source', content)
        self.assertIn('Status', content)
        self.assertIn(str(self.dataset.id), content)
        self.assertIn(self.dataset.name, content)
    
    def test_dataset_download_view_invalid_dataset(self):
        """Test GET request with invalid dataset ID"""
        url = reverse('django_app_ml:dataset-download', kwargs={'dataset_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Dataset non trouvé')


class FormTests(TestCase):
    """Tests for forms"""
    
    def setUp(self):
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
    
    def test_dataset_form_valid(self):
        """Test DatasetForm with valid data"""
        form_data = {
            'name': 'Test Dataset Form',
            'description': 'Test dataset form description',
            'link': 'https://example.com/form-dataset'
        }
        form = DatasetForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_dataset_form_invalid(self):
        """Test DatasetForm with invalid data"""
        form_data = {
            'name': '',  # Invalid: empty name
            'description': 'Test description',
            'link': 'invalid-url'  # Invalid URL
        }
        form = DatasetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('link', form.errors)
    
    def test_model_ia_form_valid(self):
        """Test ModelIAForm with valid data"""
        form_data = {
            'name': 'Test Model Form',
            'description': 'Test model form description',
            'dataset': self.dataset.id
        }
        form = ModelIAForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_model_ia_form_invalid(self):
        """Test ModelIAForm with invalid data"""
        form_data = {
            'name': '',  # Invalid: empty name
            'description': 'Test description',
            'dataset': 99999  # Invalid: non-existent dataset
        }
        form = ModelIAForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('dataset', form.errors)


class SerializerTests(TestCase):
    """Tests for serializers"""
    
    def setUp(self):
        self.dataset = DataSet.objects.create(
            name='Test Dataset',
            description='Test dataset description',
            link='https://example.com/dataset'
        )
        
        self.model = IAModel.objects.create(
            name='Test Model',
            description='Test model description',
            dataset=self.dataset
        )
    
    def test_dataset_serializer(self):
        """Test DatasetSerializer"""
        serializer = DatasetSerializer(self.dataset)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Dataset')
        self.assertEqual(data['description'], 'Test dataset description')
        self.assertEqual(data['link'], 'https://example.com/dataset')
    
    def test_iamodel_serializer(self):
        """Test IAModelSerializer"""
        serializer = IAModelSerializer(self.model)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Model')
        self.assertEqual(data['description'], 'Test model description')
        self.assertEqual(data['dataset'], self.dataset.id)
    
    def test_task_serializer(self):
        """Test TaskSerializer"""
        task = Task.objects.create(
            actor_name='test_actor',
            queue_name='test_queue',
            status=Task.STATUS_ENQUEUED
        )
        serializer = TaskSerializer(task)
        data = serializer.data
        
        self.assertEqual(data['actor_name'], 'test_actor')
        self.assertEqual(data['queue_name'], 'test_queue')
        self.assertEqual(data['status'], Task.STATUS_ENQUEUED)
        self.assertIn('url', data)
        self.assertIn('message', data)

