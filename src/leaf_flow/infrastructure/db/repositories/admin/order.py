from decimal import Decimal
from typing import Any, Sequence

from sqlalchemy import or_, select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from leaf_flow.application.ports.admin.order import AdminOrderReader, AdminOrderWriter
from leaf_flow.domain.entities.order import OrderEntity
from leaf_flow.infrastructure.db.mappers.order import map_order_model_to_entity
from leaf_flow.infrastructure.db.models.order import Order, OrderItem, OrderStatusEnum
from leaf_flow.infrastructure.db.repositories.base import Repository


def _escape_like(value: str) -> str:
    """Экранирование спецсимволов для LIKE/ILIKE запросов."""
    return value.replace(
        "\\",
        "\\\\"
    ).replace("%", r"\%").replace("_", r"\_")


class AdminOrderReaderRepository(Repository[Order], AdminOrderReader):
    """Репозиторий для чтения заказов в админке."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    @staticmethod
    def _order_load_options():
        """Опции загрузки для Order с items, product и variant."""
        return selectinload(Order.items).options(
            selectinload(OrderItem.product),
            selectinload(OrderItem.variant),
        )

    async def get_by_id(self, order_id: str) -> OrderEntity | None:
        """Получить заказ по ID с загрузкой items."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(self._order_load_options())
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
        """Получить список заказов с фильтрацией и пагинацией."""
        stmt = select(Order).options(self._order_load_options())
        count_stmt = select(func.count(Order.id))

        if search:
            escaped = _escape_like(search)
            search_filter = or_(
                Order.id.ilike(f"%{escaped}%", escape="\\"),
                Order.customer_name.ilike(f"%{escaped}%", escape="\\"),
                Order.phone.ilike(f"%{escaped}%", escape="\\"),
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
    """Репозиторий для записи заказов в админке."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    @staticmethod
    def _order_load_options():
        """Опции загрузки для Order с items, product и variant."""
        return selectinload(Order.items).options(
            selectinload(OrderItem.product),
            selectinload(OrderItem.variant),
        )

    async def _get_order_with_items(self, order_id: str) -> OrderEntity:
        """Получить заказ с items после изменения."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(self._order_load_options())
        )
        order_model = (await self.session.execute(stmt)).scalar_one()
        return map_order_model_to_entity(order_model)

    async def update(self, order_id: str, **fields: object) -> OrderEntity | None:
        """Обновить поля заказа."""
        allowed = set(Order.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = update(Order).where(Order.id == order_id).values(**values)
        await self.session.execute(stmt)
        await self.session.flush()

        return await self._get_order_with_items(order_id)

    async def update_status(self, order_id: str, status: str) -> OrderEntity:
        """Обновить статус заказа."""
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(status=OrderStatusEnum(status))
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return await self._get_order_with_items(order_id)

    async def update_items(
        self,
        order_id: str,
        items: list[dict[str, Any]],
        total: Decimal
    ) -> OrderEntity:
        """Заменить items заказа и обновить total."""
        # 1. Обновляем total заказа
        await self.session.execute(
            update(Order).where(Order.id == order_id).values(total=total)
        )

        # 2. Удаляем старые items
        await self.session.execute(
            delete(OrderItem).where(OrderItem.order_id == order_id)
        )

        # 3. Добавляем новые items
        for item_data in items:
            item = OrderItem(
                order_id=order_id,
                product_id=item_data["product_id"],
                variant_id=item_data["variant_id"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                total=item_data["price"] * item_data["quantity"],
            )
            self.session.add(item)

        await self.session.flush()
        return await self._get_order_with_items(order_id)

    async def delete_items(self, order_id: str) -> None:
        """Удалить все items заказа."""
        stmt = delete(OrderItem).where(OrderItem.order_id == order_id)
        await self.session.execute(stmt)
        await self.session.flush()
