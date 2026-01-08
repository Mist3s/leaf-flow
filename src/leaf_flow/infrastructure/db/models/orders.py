from decimal import Decimal
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Enum as SAEnum, ForeignKey, Numeric, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from leaf_flow.infrastructure.db.base import Base


class DeliveryMethodEnum(str, PyEnum):  # type: ignore[misc]
    pickup = "pickup"
    courier = "courier"
    cdek = "cdek"


class OrderStatusEnum(str, PyEnum):  # type: ignore[misc]
    created = "created"
    processing = "processing"
    paid = "paid"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    delivery: Mapped[DeliveryMethodEnum] = mapped_column(SAEnum(DeliveryMethodEnum, name="delivery_method"))
    address: Mapped[str | None] = mapped_column(String(1024), default=None)
    comment: Mapped[str | None] = mapped_column(String(500), default=None)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[OrderStatusEnum] = mapped_column(SAEnum(OrderStatusEnum, name="order_status"), default=OrderStatusEnum.created, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        # Составной индекс для частого запроса "заказы пользователя с сортировкой по дате"
        Index("ix_orders_user_id_created_at", "user_id", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(String(64))
    variant_id: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="items")


