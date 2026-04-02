from celery import Celery
from leaf_flow.config import settings


celery_client = Celery(
    "leaf_flow_client",
    broker=settings.REDIS_URL
)
