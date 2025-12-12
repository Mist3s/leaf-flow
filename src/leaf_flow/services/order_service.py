from decimal import Decimal
from uuid import uuid4
from typing import Iterable

from leaf_flow.infrastructure.db.models.orders import (
    Order, OrderItem, DeliveryMethodEnum, OrderStatusEnum
)
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.cart_service import get_cart, clear_cart
from leaf_flow.domain.entities.order import OrderEntity
from leaf_flow.domain.mappers import map_order_model_to_entity


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
    order_id = uuid4().hex
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
    return map_order_model_to_entity(order, order_items)


async def get_order(order_id: str, uow: UoW) -> tuple[OrderEntity | None]:
    order = await uow.orders.get_with_items(order_id)
    if not order:
        return (None,)
    items = await uow.order_items.list_for_order(order_id)
    return (map_order_model_to_entity(order, items),)


async def list_orders_for_user(user_id: int, limit: int, offset: int, uow: UoW) -> list[OrderEntity]:
    orders = await uow.orders.list_for_user(user_id=user_id, limit=limit, offset=offset)
    entities: list[OrderEntity] = []
    for order in orders:
        entities.append(
            OrderEntity(
                id=order.id,
                customer_name=order.customer_name,
                phone=order.phone,
                delivery=order.delivery.value,  # type: ignore[assignment]
                total=order.total,
                items=[],
                address=order.address,
                comment=order.comment,
                status=order.status.value,  # type: ignore[assignment]
                created_at=order.created_at,
            )
        )
    return entities
