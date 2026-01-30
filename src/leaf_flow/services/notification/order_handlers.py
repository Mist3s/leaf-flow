"""
Обработчики событий заказов.

Подгружают данные пользователя и отправляют уведомления в Celery.
"""
import logging
from abc import ABC
from typing import Any

from leaf_flow.application.events.base import EventHandler
from leaf_flow.application.events.factory import EventHandlerFactory
from leaf_flow.infrastructure.externals.celery.celery_client import celery_client
from leaf_flow.application.dto.notification import NotificationsOrderEntity

logger = logging.getLogger(__name__)


class OrderEventHandlerBase(EventHandler, ABC):
    """Базовый обработчик для событий заказов."""

    async def _get_user(self, user_id: int):
        """Получить пользователя по ID."""
        return await self._uow.users_reader.get_by_id(user_id)

    async def _get_support_topic(self, telegram_id: int | None):
        """Получить support topic по telegram_id."""
        if not telegram_id:
            return None
        return await self._uow.support_topics_reader.get_by_user_telegram_id(telegram_id)

    @staticmethod
    def _send_notifications(payload: dict[str, Any]) -> None:
        """Отправить уведомления в Celery."""
        celery_client.send_task(
            "notifications.send_notification.order.admin",
            args=[payload],
            queue="notifications"
        )
        celery_client.send_task(
            "notifications.send_notification.order.user",
            args=[payload],
            queue="notifications"
        )


class OrderCreatedHandler(OrderEventHandlerBase):
    """Обработчик события order.created."""

    async def handle(self, payload: dict[str, Any]) -> None:
        order_id = payload["order_id"]
        user_id = payload["user_id"]

        # Подгружаем только данные пользователя
        user = await self._get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for order {order_id}")
            return

        support_topic = await self._get_support_topic(user.telegram_id)

        # Используем from_outbox_payload
        entity = NotificationsOrderEntity.from_outbox_payload(
            payload=payload,
            telegram_id=user.telegram_id,
            email=user.email,
            admin_chat_id=support_topic.admin_chat_id if support_topic else None,
            thread_id=support_topic.thread_id if support_topic else None,
            old_status=payload["status"],
            new_status=payload["status"],
        )

        self._send_notifications(entity.to_payload())
        logger.info(f"Sent order.created notifications for order {order_id}")


class OrderStatusChangedHandler(OrderEventHandlerBase):
    """Обработчик события order.status_changed."""

    async def handle(self, payload: dict[str, Any]) -> None:
        order_id = payload["order_id"]
        user_id = payload["user_id"]

        # Подгружаем только данные пользователя
        user = await self._get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for order {order_id}")
            return

        support_topic = await self._get_support_topic(user.telegram_id)

        # Используем from_outbox_payload
        entity = NotificationsOrderEntity.from_outbox_payload(
            payload=payload,
            telegram_id=user.telegram_id,
            email=user.email,
            admin_chat_id=support_topic.admin_chat_id if support_topic else None,
            thread_id=support_topic.thread_id if support_topic else None,
            old_status=payload["old_status"],
            new_status=payload["new_status"],
            status_comment=payload.get("status_comment"),
        )

        self._send_notifications(entity.to_payload())
        logger.info(f"Sent order.status_changed notifications for order {order_id}")


# Регистрация обработчиков
EventHandlerFactory.register("order.created", OrderCreatedHandler)
EventHandlerFactory.register("order.status_changed", OrderStatusChangedHandler)
