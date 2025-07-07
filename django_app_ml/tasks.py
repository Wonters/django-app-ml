import logging
import dramatiq
import pandas as pd
from .ml import train, predict
logger = logging.getLogger(__name__)

@dramatiq.actor(queue_name="train",
                max_retries=0,
                min_backoff=1000,
                time_limit=60000*3,
                actor_name="ml_app.train_task")
def train_task(dataset_path:str, checkpoint: ""):
    """"""
    logger.info(f"Train dataset: {dataset_path}, save on {checkpoint}")
    df_train = pd.read_parquet(dataset_path)
    train(df_train, checkpoint)

@dramatiq.actor(queue_name="predict",
                max_retries=0,
                actor_name="ml_app.predict_task",
                min_backoff=1000, time_limit=60000*3)
def predict_task(checkpoint, client):
    return predict(checkpoint, client)