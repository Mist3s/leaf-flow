import random
import string
from decimal import Decimal
from typing import Iterable

from leaf_flow.infrastructure.db.models.orders import (
    Order, OrderItem, DeliveryMethodEnum, OrderStatusEnum
)
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.cart_service import get_cart, clear_cart
from leaf_flow.domain.entities.order import OrderEntity
from leaf_flow.domain.mappers import map_order_model_to_entity
from leaf_flow.services.notification_service import (
    send_order_status_notification,
    send_website_order_notification,
)

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
        if not await uow.orders.get(order_id):  # type: ignore[assignment]
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
    delivery: DeliveryMethodEnum,
    address: str | None,
    comment: str | None,
    expected_total: Decimal | None,
    uow: UoW,
) -> OrderEntity:
    cart = await get_cart(user_id, uow)
    if not cart.items:
        raise ValueError("CART_EMPTY")
    _ensure_totals_match(
        [
            type("X", (), {"price": it.price, "quantity": it.quantity})  # minimal adapter
            for it in cart.items
        ],
        expected_total,
    )
    order_id = await generate_unique_order_id(uow)
    order = Order(
        id=order_id,
        user_id=user_id,
        customer_name=customer_name,
        phone=phone,
        delivery=delivery,
        address=address,
        comment=comment,
        total=cart.total_price,
        status=OrderStatusEnum.created,
    )
    order_items = [
        OrderItem(
            order_id=order_id,
            product_id=it.product_id,
            variant_id=it.variant_id,
            quantity=it.quantity,
            price=it.price,
            total=it.total,
        )
        for it in cart.items
    ]
    await uow.orders.add_with_items(order, order_items)
    await uow.commit()
    await clear_cart(user_id, uow)

    order_db = await uow.orders.get_with_items(order_id)

    if not order_db:
        raise ValueError("ORDER_NOT_FOUND")
    
    # Отправляем уведомление о создании заказа
    user = await uow.users.get(user_id)
    if user and user.telegram_id is not None:
        # Type narrowing: после проверки user.telegram_id гарантированно не None
        telegram_id = user.telegram_id
        await send_order_status_notification(
            order_id=order_id,
            user_telegram_id=telegram_id,
            new_status="created",
            comment=comment,
        )
    elif user and user.email is not None:
        # Пользователь зарегистрирован через сайт (по email)
        await send_website_order_notification(
            order_id=order_id,
            email=user.email,
            phone=phone,
            customer_name=customer_name,
            total=str(cart.total_price),
            delivery_method=delivery.value,
            comment=comment,
        )
    
    return map_order_model_to_entity(order_db)


async def get_order(order_id: str, uow: UoW) -> OrderEntity | None:
    order = await uow.orders.get_with_items(order_id)

    if not order:
        return None

    return map_order_model_to_entity(order)


async def list_orders_for_user(user_id: int, limit: int, offset: int, uow: UoW) -> list[OrderEntity]:
    orders = await uow.orders.list_for_user(user_id=user_id, limit=limit, offset=offset)
    entities: list[OrderEntity] = []
    for order in orders:
        entities.append(map_order_model_to_entity(order))
    return entities


async def update_order_status(
    order_id: str,
    new_status: OrderStatusEnum,
    comment: str | None,
    uow: UoW,
) -> OrderEntity:
    """
    Обновляет статус заказа и отправляет уведомление во внешний API.

    Args:
        order_id: ID заказа
        new_status: Новый статус заказа
        comment: Опциональный комментарий к изменению статуса
        uow: Unit of Work

    Returns:
        OrderEntity: Обновленная сущность заказа

    Raises:
        ValueError: Если заказ не найден
    """
    order = await uow.orders.get_with_items(order_id)
    if not order:
        raise ValueError("ORDER_NOT_FOUND")
    
    order.status = new_status
    await uow.commit()
    
    # Отправляем уведомление о смене статуса
    if order.user_id:
        user = await uow.users.get(order.user_id)
        if user and user.telegram_id is not None:
            # Type narrowing: после проверки user.telegram_id гарантированно не None
            telegram_id = user.telegram_id
            await send_order_status_notification(
                order_id=order_id,
                user_telegram_id=telegram_id,
                new_status=new_status.value,
                comment=comment,
            )

    return map_order_model_to_entity(order)
