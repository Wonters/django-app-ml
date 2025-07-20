import io
import logging
from functools import lru_cache
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
import pandas as pd
from rest_framework import status
from django_dramatiq.models import Task
from .models import ParquetBase
from .decorator import timer
from .task_utils import TaskResultManager

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


class TaskViewMixin:
    """
    Mixin for generalizing task management functionality.
    
    Provides common methods for:
    - _format_task_response: Standardized task response formatting
    - launch_task: Launch a task with given parameters
    - get_task_status: Get the status of a task
    """
    
    def _format_task_response(
        self, status, message, task_id, error=None, result=None, http_status=200
    ):
        """
        Format a standardized task response.

        Args:
            status (str): Task status ('pending', 'running', 'completed', 'failed', 'unknown')
            message (str): Human-readable message
            task_id (str): Task identifier
            error (str, optional): Error message if applicable
            result (dict, optional): Task result data
            http_status (int): HTTP status code

        Returns:
            Response: Formatted JSON response
        """
        response_data = {"status": status, "message": message, "task_id": task_id}

        if error is not None:
            response_data["error"] = error

        if result is not None:
            response_data["result"] = result

        return Response(response_data, status=http_status)

    def launch_task(self, task_func, task_kwargs, success_message, error_message):
        """
        Launch a task with the given parameters.

        Args:
            task_func: The task function to execute
            task_kwargs (dict): Keyword arguments for the task
            success_message (str): Success message to return
            error_message (str): Error message to return

        Returns:
            Response: Formatted task response
        """
        try:
            task = task_func.send_with_options(kwargs=task_kwargs)
            return self._format_task_response(
                status="pending",
                message=success_message,
                task_id=task.message_id,
            )
        except Exception as e:
            logger.error(f"Erreur lors du lancement de la tâche: {e}")
            return self._format_task_response(
                status="failed",
                message=error_message,
                task_id=None,
                error=str(e),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_task_status(self, task_id, task_name="Tâche"):
        """
        Get the status of a task.

        Args:
            task_id (str): Task identifier
            task_name (str): Human-readable task name for messages

        Returns:
            Response: Formatted task status response
        """
        try:
            task = Task.tasks.get(id=task_id)
            task_manager = TaskResultManager()

            # Check task status from django_dramatiq Task model
            if task.status == Task.STATUS_ENQUEUED:
                return self._format_task_response(
                    status="pending",
                    message=f"{task_name} en attente de traitement",
                    task_id=task_id,
                )

            elif task.status == Task.STATUS_RUNNING:
                return self._format_task_response(
                    status="running",
                    message=f"{task_name} en cours d'exécution",
                    task_id=task_id,
                )

            elif task.status == Task.STATUS_DONE:
                # Task completed, get the result
                result = task_manager.get_task_result(task_id)
                logger.info(f"Task result: {result}")

                # Check if result exists and contains error information
                if result is not None:
                    # Check if the result contains error information
                    if isinstance(result, dict):
                        if "error" in result and result["error"]:
                            # Task completed but with errors
                            error_message = (
                                result.get("error")
                                or result.get("exception")
                                or result.get("failed")
                                or "Erreur inconnue"
                            )
                            return self._format_task_response(
                                status="failed",
                                message=f"{task_name} terminée avec des erreurs",
                                task_id=task_id,
                                error=error_message,
                                result=result,
                                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )
                        else:
                            # Task completed successfully with results
                            return self._format_task_response(
                                status="completed",
                                message=f"{task_name} terminée avec succès",
                                task_id=task_id,
                                result=result,
                            )
                    elif isinstance(result, Exception):
                        # Result is an exception object
                        return self._format_task_response(
                            status="failed",
                            message=f"{task_name} terminée avec une exception",
                            task_id=task_id,
                            error=str(result),
                            result={"exception": str(result)},
                            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    else:
                        # Result exists but is not a dict or exception - assume success
                        return self._format_task_response(
                            status="completed",
                            message=f"{task_name} terminée avec succès",
                            task_id=task_id,
                            result=result,
                        )
                else:
                    # No result available - this could indicate a problem
                    return self._format_task_response(
                        status="completed",
                        message=f"{task_name} terminée mais aucun résultat disponible",
                        task_id=task_id,
                        result={"warning": "Aucun résultat retourné par la tâche"},
                    )

            elif task.status == Task.STATUS_FAILED:
                # Task failed, get error details
                error_message = task.error or "Erreur inconnue"
                result_data = None

                # Try to get more detailed error information
                try:
                    result = task_manager.get_task_result(task_id)
                    if result and isinstance(result, dict) and "error" in result:
                        error_message = result["error"]
                        result_data = result
                except:
                    pass

                return self._format_task_response(
                    status="failed",
                    message=f"{task_name} échouée",
                    task_id=task_id,
                    error=error_message,
                    result=result_data,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            else:
                # Unknown status
                return self._format_task_response(
                    status="unknown",
                    message=f"Statut inconnu: {task.status}",
                    task_id=task_id,
                )

        except Task.DoesNotExist:
            return self._format_task_response(
                status="failed",
                message="Tâche non trouvée",
                task_id=task_id,
                error="Tâche non trouvée",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut de la tâche {task_id}: {e}")
            return self._format_task_response(
                status="failed",
                message="Erreur lors de la récupération du statut",
                task_id=task_id,
                error=str(e),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


