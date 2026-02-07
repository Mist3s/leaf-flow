"""
Обработчики событий изображений.

Отправляет задачу на создание вариантов изображения в Celery.
"""
import logging
from typing import Any

from leaf_flow.application.events.base import EventHandler
from leaf_flow.application.events.factory import EventHandlerFactory
from leaf_flow.infrastructure.externals.celery.celery_client import celery_client

logger = logging.getLogger(__name__)


class ImageUploadedHandler(EventHandler):
    """
    Обработчик события image.uploaded.
    
    Отправляет задачу в Celery для создания вариантов изображения
    (thumb, md, lg).
    """

    async def handle(self, payload: dict[str, Any]) -> None:
        image_id = payload["image_id"]
        product_id = payload["product_id"]
        
        logger.info(
            f"Processing image.uploaded event for image_id={image_id}, "
            f"product_id={product_id}"
        )
        
        # Отправляем задачу в Celery для создания вариантов
        celery_client.send_task(
            "images.create_variants",
            args=[payload],
            queue="images"
        )
        
        logger.info(f"Sent images.create_variants task for image_id={image_id}")


# Регистрация обработчика
EventHandlerFactory.register("image.uploaded", ImageUploadedHandler)
