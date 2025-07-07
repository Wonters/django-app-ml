from rest_framework.serializers import (ModelSerializer,
                                        Serializer,
                                        HyperlinkedIdentityField,
                                        SerializerMethodField,
                                        )
from rest_framework.fields import FileField
from django.urls import reverse
from django_dramatiq.models import Task
from .models import Client

class ClientSerializer(ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"

class ClientPredictSerializer(ModelSerializer):
    class Meta:
        model =Client
        exclude = ['TARGET']

class ClientUploadSerializer(Serializer):
    file = FileField()


class TaskSerializer(ModelSerializer):
    url = HyperlinkedIdentityField(view_name='ml_app:task-detail', lookup_field="id")
    message = SerializerMethodField()
    class Meta:
        model = Task
        fields = [
            'url', 'id', 'actor_name', 'queue_name',
            'status', 'created_at', 'message'
        ]

    def get_message(self, obj):
        return obj.message.asdict()