from celery import Celery
from leaf_flow.config import settings


celery_client = Celery(
    "leaf_flow_client",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
)
