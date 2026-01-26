import random
import string
from decimal import Decimal
from typing import Iterable, Sequence

from celery import Celery

from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.cart_service import get_cart, clear_cart
from leaf_flow.domain.entities.order import OrderEntity, DeliveryMethod, OrderStatus
from leaf_flow.infrastructure.externals.celery.notification import map_notifications_order_to_entity

LETTERS = string.ascii_uppercase
DIGITS = string.digits
ALPHABET = LETTERS + DIGITS

def generate_order_id(length: int = 8) -> str:
    if length < 2:
        raise ValueError("length must be >= 2 to include both letter and digit")

    chars = [random.choice(LETTERS), random.choice(DIGITS)]
    chars += random.choices(ALPHABET, k=length - 2)
    random.shuffle(chars)
    return "".join(chars)


async def generate_unique_order_id(uow: UoW, length: int = 8, max_tries: int = 50) -> str:
    for _ in range(max_tries):
        order_id = generate_order_id(length)
        if not await uow.orders_reader.get_order_with_items(order_id):
            return order_id
    raise RuntimeError("FAILED_TO_GENERATE_UNIQUE_ORDER_ID")


def _ensure_totals_match(items: Iterable, expected_total: Decimal | None) -> None:
    if expected_total is None:
        return
    calc_total = Decimal("0.00")
    for it in items:
        calc_total += (it.price or Decimal("0.00")) * it.quantity
    if calc_total != expected_total:
        raise ValueError("TOTAL_MISMATCH")


async def create_order(
    user_id: int,
    customer_name: str,
    phone: str,
    delivery: DeliveryMethod,
    address: str | None,
    comment: str | None,
    expected_total: Decimal | None,
    uow: UoW,
    celery: Celery
) -> OrderEntity:
    cart = await get_cart(user_id, uow)
    if not cart.items:
        raise ValueError("CART_EMPTY")
    _ensure_totals_match(cart.items, expected_total)
    order_id = await generate_unique_order_id(uow)
    order = await uow.orders_writer.create_order_with_items(
        cart=cart,
        order_id=order_id,
        user_id=user_id,
        customer_name=customer_name,
        phone=phone,
        delivery=delivery,
        address=address,
        comment=comment
    )
    await uow.commit()
    await clear_cart(user_id, uow)

    if not order:
        raise ValueError("ORDER_NOT_FOUND")
    
    # Отправляем уведомление о создании заказа
    user = await uow.users_reader.get_by_id(user_id)
    support_topic = await uow.support_topics_reader.get_by_user_telegram_id(
        user.telegram_id
    ) if user.telegram_id else None

    entity = map_notifications_order_to_entity(
        order=order,
        user=user,
        old_status=order.status,
        support_topic=support_topic
    )


    celery.send_task(
        "notifications.send_notification.order.admin",
        args=[entity.to_payload()],
        queue="notifications"
    )
    celery.send_task(
        "notifications.send_notification.order.user",
        args=[entity.to_payload()],
        queue="notifications"
    )
    
    return order


async def get_order(order_id: str, uow: UoW) -> OrderEntity | None:
    order = await uow.orders_reader.get_order_with_items(order_id)

    if not order:
        return None

    return order


async def list_orders_for_user(
    user_id: int,
    limit: int,
    offset: int,
    uow: UoW
) -> Sequence[OrderEntity]:
    orders = await uow.orders_reader.list_orders_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return orders


async def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    comment: str | None,
    uow: UoW,
    celery: Celery
) -> OrderEntity:
    """
    Обновляет статус заказа и отправляет уведомление во внешний API.

    Args:
        order_id: ID заказа
        new_status: Новый статус заказа
        comment: Опциональный комментарий к изменению статуса
        uow: Unit of Work
        celery: Celery client

    Returns:
        OrderEntity: Обновленная сущность заказа

    Raises:
        ValueError: Если заказ не найден
    """
    order = await uow.orders_reader.get_order_with_items(
        order_id=order_id
    )

    if not order:
        raise ValueError("ORDER_NOT_FOUND")

    old_status = order.status
    order = await uow.orders_writer.update_order_status(
        order_id=order_id,
        new_status=new_status
    )
    await uow.commit()

    user = await uow.users_reader.get_by_id(order.user_id)
    support_topic = await uow.support_topics_reader.get_by_user_telegram_id(
        user.telegram_id
    ) if user.telegram_id else None

    entity = map_notifications_order_to_entity(
        order=order,
        user=user,
        old_status=old_status,
        status_comment=comment,
        support_topic=support_topic
    )

    celery.send_task(
        "notifications.send_notification.order.admin",
        args=[entity.to_payload()],
        queue="notifications"
    )
    celery.send_task(
        "notifications.send_notification.order.user",
        args=[entity.to_payload()],
        queue="notifications"
    )

    return order
