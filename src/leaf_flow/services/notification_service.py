import logging
from typing import Optional

import httpx

from leaf_flow.config import settings

logger = logging.getLogger(__name__)


async def send_order_status_notification(
    order_id: str,
    user_telegram_id: int,
    new_status: str,
    comment: Optional[str] = None,
) -> None:
    """
    Отправляет уведомление о смене статуса заказа во внешний BOT.

    Args:
        order_id: ID заказа
        user_telegram_id: Telegram ID пользователя
        new_status: Новый статус заказа
        comment: Опциональный комментарий к изменению статуса
    """
    url = f"{settings.EXTERNAL_BOT_URL}/internal/order-status-changed"
    headers = {
        "Authorization": f"Bearer {settings.EXTERNAL_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "orderId": order_id,
        "userTelegramId": user_telegram_id,
        "newStatus": new_status,
    }
    if comment:
        payload["comment"] = comment

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(
                f"Order status notification sent successfully for order {order_id}, "
                f"status: {new_status}"
            )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to send order status notification: HTTP {e.response.status_code}, "
            f"order_id={order_id}, status={new_status}"
        )
    except httpx.RequestError as e:
        logger.error(
            f"Failed to send order status notification: Request error {e}, "
            f"order_id={order_id}, status={new_status}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error sending order status notification: {e}, "
            f"order_id={order_id}, status={new_status}"
        )


async def send_website_order_notification(
    order_id: str,
    email: str,
    phone: str,
    customer_name: str,
    total: str,
    delivery_method: str,
    comment: Optional[str] = None,
) -> None:
    """
    Отправляет уведомление о заказе с сайта во внешний BOT.
    Используется для пользователей без Telegram ID (зарегистрированных по email).

    Args:
        order_id: ID заказа
        email: Email пользователя
        phone: Телефон пользователя
        customer_name: Имя покупателя
        total: Сумма заказа
        delivery_method: Способ доставки
        comment: Опциональный комментарий к заказу
    """
    url = f"{settings.EXTERNAL_BOT_URL}/internal/website-order-created"
    headers = {
        "Authorization": f"Bearer {settings.EXTERNAL_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "orderId": order_id,
        "email": email,
        "phone": phone,
        "customerName": customer_name,
        "total": total,
        "deliveryMethod": delivery_method,
    }
    if comment:
        payload["comment"] = comment

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(
                f"Website order notification sent successfully for order {order_id}"
            )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to send website order notification: HTTP {e.response.status_code}, "
            f"order_id={order_id}"
        )
    except httpx.RequestError as e:
        logger.error(
            f"Failed to send website order notification: Request error {e}, "
            f"order_id={order_id}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error sending website order notification: {e}, "
            f"order_id={order_id}"
        )

