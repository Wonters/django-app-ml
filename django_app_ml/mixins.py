import io
import logging
from functools import lru_cache
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
import pandas as pd
from .models import ParquetBase
from .decorator import timer

logger = logging.getLogger(__name__)

class ParquetQuerySetMixin:
    """
    Hook queryset system to work with parquet
    """
    queryset = None
    @timer
    @lru_cache(maxsize=5)
    def _get_queryset(self) -> pd.DataFrame:
        try:
            object = ParquetBase.objects.get(model_link=self.queryset.model.__name__)
        except ObjectDoesNotExist:
            df = pd.DataFrame.from_records(self.queryset.values())
            buffer = io.BytesIO()
            df.to_parquet(buffer)
            buffer.seek(0)
            object = ParquetBase(model_link=self.queryset.model.__name__,
                        file=ContentFile(buffer.read(), name=f"{self.queryset.model.__name__}.parquet"))
            object.save()
            return self.get_queryset()
        return pd.read_parquet(object.file.path)

    def get_queryset(self):
        return self._get_queryset()



class ParquetViewSetMixin(ModelViewSet, ParquetQuerySetMixin):
    def filter_queryset(self, queryset):
        """
        Given a parquet, filter it with whichever filter backend is in use.
        #todo : show filter_backends = api_settings.DEFAULT_FILTER_BACKENDS
        """
        super().filter_queryset(queryset)
        return self.queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset.to_dict(orient="records"))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


