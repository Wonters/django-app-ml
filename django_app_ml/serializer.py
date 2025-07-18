from rest_framework.serializers import (ModelSerializer,
                                        Serializer,
                                        HyperlinkedIdentityField,
                                        SerializerMethodField,
                                        HyperlinkedRelatedField,
                                        )
from rest_framework.fields import FileField
from django.urls import reverse
from django_dramatiq.models import Task
from .models import DataSet, IAModel, Bucket

class IAModelSerializer(ModelSerializer):
    class Meta:
        model = IAModel
        fields = "__all__"

class BucketSerializer(ModelSerializer):
    id = HyperlinkedIdentityField(view_name='django_app_ml:bucket-detail', lookup_field="id")
    class Meta:
        model = Bucket
        fields = "__all__"

class DatasetSerializer(ModelSerializer):
    id = HyperlinkedIdentityField(view_name='django_app_ml:dataset-detail', lookup_field="id")
    bucket = HyperlinkedRelatedField(
        view_name='django_app_ml:bucket-detail',
        lookup_field='id',
        read_only=True
    )
    
    class Meta:
        model = DataSet
        fields = "__all__"


class TaskSerializer(ModelSerializer):
    url = HyperlinkedIdentityField(view_name='django_app_ml:task-detail', lookup_field="id")
    message = SerializerMethodField()
    class Meta:
        model = Task
        fields = [
            'url', 'id', 'actor_name', 'queue_name',
            'status', 'created_at', 'message'
        ]

    def get_message(self, obj):
        return obj.message.asdict()