from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.order import OrderReader, OrderWriter
from leaf_flow.domain.entities.cart import CartDetailEntity
from leaf_flow.domain.entities.order import OrderEntity, DeliveryMethod, OrderStatus
from leaf_flow.infrastructure.db.mappers.order import map_order_model_to_entity
from leaf_flow.infrastructure.db.models.order import (
    Order, OrderItem, OrderStatusEnum, DeliveryMethodEnum
)
from leaf_flow.infrastructure.db.repositories.base import Repository


class OrderReaderRepository(Repository[Order], OrderReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def get_order_with_items(
        self,
        order_id: str
    ) -> OrderEntity | None:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.items).selectinload(OrderItem.variant),
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .where(Order.id == order_id)
        )
        order = (await self.session.execute(stmt)).scalar_one_or_none()

        if not order:
            return None

        return map_order_model_to_entity(order)

    async def list_orders_by_user(
        self,
        user_id: int,
        limit: int,
        offset: int
    ) -> Sequence[OrderEntity]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.items).selectinload(OrderItem.variant),
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        orders = (await self.session.execute(stmt)).scalars().all()
        return [map_order_model_to_entity(order) for order in orders]


class OrderWriterRepository(Repository[Order], OrderWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def create_order_with_items(
        self,
        cart: CartDetailEntity,
        order_id: str,
        user_id: int,
        customer_name: str,
        delivery: DeliveryMethod,
        phone: str,
        address: str | None,
        comment: str | None
    ) -> OrderEntity:
        order = Order(
            id=order_id,
            user_id=user_id,
            customer_name=customer_name,
            phone=phone,
            delivery=DeliveryMethodEnum(delivery),
            address=address,
            comment=comment,
            total=cart.total_price,
            status=OrderStatusEnum.created,
        )
        order.items = [
            OrderItem(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
            )
            for it in cart.items
        ]

        self.session.add(order)
        await self.session.flush()

        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.variant)
            )
        )
        order = (await self.session.scalars(stmt)).one()
        return map_order_model_to_entity(order)

    async def transfer_orders_to_user(self, from_user_id: int, to_user_id: int) -> int:
        stmt = (
            update(Order)
            .where(Order.user_id == from_user_id)
            .values(user_id=to_user_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus
    ) -> OrderEntity:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.variant)
            )
        )
        order = (await self.session.scalars(stmt)).one()
        order.status = OrderStatusEnum(new_status)
        await self.session.flush()
        return map_order_model_to_entity(order)
