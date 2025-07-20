from rest_framework.exceptions import APIException
from rest_framework import status


class AuditDatasetException(APIException):
    """
    Exception personnalisée pour les erreurs d'audit de dataset.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Une erreur s'est produite lors de l'audit du dataset."
    default_code = "audit_dataset_error"

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code)

    @staticmethod
    def exception_to_dict(exc: APIException) -> dict:
        return {
            "detail": exc.detail,
            "code": exc.get_codes(),
            "status_code": exc.status_code,
        }


class DatasetNotFoundError(AuditDatasetException):
    """
    Exception levée quand un dataset n'est pas trouvé.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Dataset non trouvé."
    default_code = "dataset_not_found"


class DatasetAccessError(AuditDatasetException):
    """
    Exception levée quand il y a un problème d'accès au dataset.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Accès refusé au dataset."
    default_code = "dataset_access_denied"


class DatasetValidationError(AuditDatasetException):
    """
    Exception levée quand le dataset ne peut pas être validé.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Le dataset ne peut pas être validé."
    default_code = "dataset_validation_error" 