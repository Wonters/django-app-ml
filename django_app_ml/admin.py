try:
    from core.custom_admin import custom_admin_site
except ImportError:
    from django.contrib import admin
    custom_admin_site = admin.site
from django_dramatiq.models import Task
from .models import ParquetBase, DataSet, IAModel
# Register your models here.

custom_admin_site.register(ParquetBase)
custom_admin_site.register(DataSet)
custom_admin_site.register(IAModel)
custom_admin_site.register(Task)