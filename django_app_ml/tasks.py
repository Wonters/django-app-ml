import logging
import dramatiq
import pandas as pd
from .logging import get_logger
from .ml import train, predict
from .dataset_audit import PandasDatasetAuditor

logger = get_logger(__name__)


@dramatiq.actor(queue_name="train",
                max_retries=0,
                min_backoff=1000,
                time_limit=60000*3,
                actor_name="ml_app.train_task")
def train_task(dataset_path: str, checkpoint: str = ""):
    """
    Call the model to train ini grpc 
    """
    logger.info(f"Train dataset: {dataset_path}, save on {checkpoint}")
    df_train = pd.read_parquet(dataset_path)
    train(df_train, checkpoint)



@dramatiq.actor(queue_name="predict",
                max_retries=0,
                actor_name="ml_app.predict_task",
                min_backoff=1000, time_limit=60000*3)
def predict_task(checkpoint, client):
    return predict(checkpoint, client)


@dramatiq.actor(queue_name="audit",
                max_retries=0,
                actor_name="ml_app.audit_task",
                min_backoff=1000, time_limit=60000*5)
def audit_dataset_task(dataset_path: str, bucket: int = None, save_report: bool = True, report_path: str = None):
    """
    Effectue un audit complet d'un dataset avec Pandas
    """
    logger.info(f"Début de l'audit du dataset: {dataset_path}")
    try:
        auditor = PandasDatasetAuditor()
        results = auditor.full_audit(dataset_path, save_report=save_report, report_path=report_path)
        logger.info(f"Audit terminé avec succès pour: {dataset_path}")
        return results
    except Exception as e:
        logger.error(f"Erreur lors de l'audit du dataset {dataset_path}: {e}")
        raise



