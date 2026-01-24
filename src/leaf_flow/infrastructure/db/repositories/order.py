from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from leaf_flow.infrastructure.db.models.order import Order, OrderItem
from leaf_flow.infrastructure.db.repositories.base import Repository


class OrderRepository(Repository[Order]):
    def __init__(self, session: Session):
        super().__init__(session, Order)

    async def transfer_orders_to_user(self, from_user_id: int, to_user_id: int) -> int:
        """
        Переносит все заказы от одного пользователя к другому.
        
        Returns:
            Количество перенесённых заказов
        """
        stmt = (
            update(Order)
            .where(Order.user_id == from_user_id)
            .values(user_id=to_user_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def add_with_items(self, order: Order, items: list[OrderItem]) -> Order:
        self.session.add(order)
        await self.session.flush()
        for it in items:
            it.order_id = order.id
            self.session.add(it)
        return order

    async def get_with_items(self, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.items).selectinload(OrderItem.variant),
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .where(Order.id == order_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(self, user_id: int, limit: int, offset: int) -> Sequence[Order]:
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
        return (await self.session.execute(stmt)).scalars().all()


class OrderItemRepository(Repository[OrderItem]):
    def __init__(self, session: Session):
        super().__init__(session, OrderItem)

    async def list_for_order(self, order_id: str) -> Sequence[OrderItem]:
        stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        return (await self.session.execute(stmt)).scalars().all()
