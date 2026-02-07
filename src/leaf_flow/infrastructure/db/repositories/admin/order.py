from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from leaf_flow.application.ports.admin.order import AdminOrderReader, AdminOrderWriter
from leaf_flow.domain.entities.order import OrderEntity
from leaf_flow.infrastructure.db.mappers.order import map_order_model_to_entity
from leaf_flow.infrastructure.db.models.order import Order, OrderItem, OrderStatusEnum
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminOrderReaderRepository(Repository[Order], AdminOrderReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def get_by_id(self, order_id: str) -> OrderEntity | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.variant),
            )
        )
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            return None
        return map_order_model_to_entity(order)

    async def list_orders(
        self,
        search: str | None,
        status: str | None,
        user_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[OrderEntity]]:
        stmt = select(Order).options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.variant),
        )
        count_stmt = select(func.count(Order.id))

        if search:
            search_filter = or_(
                Order.id.ilike(f"%{search}%"),
                Order.customer_name.ilike(f"%{search}%"),
                Order.phone.ilike(f"%{search}%"),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if status:
            stmt = stmt.where(Order.status == OrderStatusEnum(status))
            count_stmt = count_stmt.where(Order.status == OrderStatusEnum(status))

        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)
            count_stmt = count_stmt.where(Order.user_id == user_id)

        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        orders = result.scalars().all()

        return total, [map_order_model_to_entity(o) for o in orders]


class AdminOrderWriterRepository(Repository[Order], AdminOrderWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def update(self, order_id: str, **fields: object) -> OrderEntity | None:
        allowed = set(Order.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(**values)
        )

        await self.session.execute(stmt)
        await self.session.flush()

        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.variant),
            )
        )
        result = await self.session.execute(stmt)
        return map_order_model_to_entity(result.scalar_one())

    async def update_status(self, order_id: str, status: str) -> OrderEntity:
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(status=OrderStatusEnum(status))
        )

        await self.session.execute(stmt)
        await self.session.flush()

        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.variant),
            )
        )
        order_model = (await self.session.execute(stmt)).scalar_one()
        return map_order_model_to_entity(order_model)

    async def update_items(
        self,
        order_id: str,
        items: list[dict[str, any]],
        total: Decimal
    ) -> OrderEntity:
        stmt = (
            update(Order).where(
                Order.id == order_id
            ).values(
                total=total,
                items=[
                    OrderItem(
                        order_id=order_id,
                        product_id=item_data["product_id"],
                        variant_id=item_data["variant_id"],
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        total=item_data['price'] * item_data['quantity'],
                    )
                    for item_data in items
                ]
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.variant),
            )
        )
        order_model = (await self.session.execute(stmt)).scalar_one()
        return map_order_model_to_entity(order_model)

    async def delete_items(
        self,
        order_id: str
    ) -> None:
        stmt = (
            delete(OrderItem)
            .where(
                Order.id == order_id
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()
