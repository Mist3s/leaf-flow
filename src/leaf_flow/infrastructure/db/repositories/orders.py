from typing import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.orders import Order, OrderItem
from leaf_flow.infrastructure.db.repositories.base import Repository


class OrderRepository(Repository[Order]):
    def __init__(self, session: Session):
        super().__init__(session, Order)

    async def add_with_items(self, order: Order, items: list[OrderItem]) -> Order:
        self.session.add(order)
        await self.session.flush()
        for it in items:
            it.order_id = order.id
            self.session.add(it)
        return order

    async def get_with_items(self, order_id: str) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()


class OrderItemRepository(Repository[OrderItem]):
    def __init__(self, session: Session):
        super().__init__(session, OrderItem)

    async def list_for_order(self, order_id: str) -> Sequence[OrderItem]:
        stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        return (await self.session.execute(stmt)).scalars().all()


