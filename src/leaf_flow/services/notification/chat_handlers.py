"""
Обработчики событий для микросервиса чата.

Принимают события из outbox'а платформы и конвертируют
их в события для Chat Service (отправка в Redis Stream).
"""
import logging
from typing import Any

from leaf_flow.application.events.base import EventHandler
from leaf_flow.application.events.factory import EventHandlerFactory
from leaf_flow.infrastructure.externals.chat.publisher import chat_event_publisher

logger = logging.getLogger(__name__)


class ChatOrderCreatedHandler(EventHandler):
    """Обработчик события order.created для чата."""

    async def handle(self, payload: dict[str, Any]) -> None:
        order_id = payload.get("order_id")
        user_id = payload.get("user_id")

        if not order_id or not user_id:
            logger.warning("Missing order_id or user_id in payload for chat")
            return

        chat_payload = {
            "user_id": user_id,
            "order_id": order_id,
        }
        await chat_event_publisher.publish("order.created", chat_payload)


class ChatOrderStatusChangedHandler(EventHandler):
    """Обработчик события order.status_changed для чата."""

    async def handle(self, payload: dict[str, Any]) -> None:
        order_id = payload.get("order_id")
        status = payload.get("new_status", payload.get("status"))
        old_status = payload.get("old_status")

        if not order_id or not status:
            logger.warning("Missing order_id or status in payload for chat")
            return

        chat_payload = {
            "order_id": order_id,
            "status": status,
        }
        if old_status:
            chat_payload["old_status"] = old_status

        await chat_event_publisher.publish("order.status_changed", chat_payload)


# Регистрация обработчиков
EventHandlerFactory.register("order.created", ChatOrderCreatedHandler)
EventHandlerFactory.register("order.status_changed", ChatOrderStatusChangedHandler)
