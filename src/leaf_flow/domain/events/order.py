"""
Доменные события заказа.

Содержат все данные заказа (snapshot), чтобы при обработке
подгружать только данные пользователя.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from leaf_flow.domain.entities.order import (
    OrderEntity,
    DeliveryMethod,
    OrderStatus
)


@dataclass(frozen=True, slots=True)
class OrderEventItem:
    """Item заказа в событии."""
    product_id: str
    variant_id: str
    quantity: int
    price: Decimal
    total: Decimal
    product_name: str
    variant_weight: str


@dataclass(frozen=True, slots=True)
class OrderCreatedEvent:
    """
    Событие создания заказа.
    
    Содержит полный snapshot заказа на момент создания.
    """
    order_id: str
    user_id: int
    customer_name: str
    phone: str
    delivery: DeliveryMethod
    total: Decimal
    address: str | None
    comment: str | None
    status: OrderStatus
    created_at: datetime
    items: list[OrderEventItem] = field(default_factory=list)
    
    def to_payload(self) -> dict[str, Any]:
        """Сериализация в JSON-совместимый dict."""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "delivery": self.delivery,
            "total": str(self.total),
            "address": self.address,
            "comment": self.comment,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "items": [
                {
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "total": str(item.total),
                    "product_name": item.product_name,
                    "variant_weight": item.variant_weight,
                }
                for item in self.items
            ]
        }
    
    @classmethod
    def from_order(cls, order: OrderEntity, user_id: int) -> "OrderCreatedEvent":
        """Создать событие из OrderEntity."""
        return cls(
            order_id=order.id,
            user_id=user_id,
            customer_name=order.customer_name,
            phone=order.phone,
            delivery=order.delivery,
            total=order.total,
            address=order.address,
            comment=order.comment,
            status=order.status,
            created_at=order.created_at or datetime.utcnow(),
            items=[
                OrderEventItem(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    product_name=item.product_name,
                    variant_weight=item.variant_weight,
                )
                for item in order.items
            ]
        )


@dataclass(frozen=True, slots=True)
class OrderStatusChangedEvent:
    """
    Событие изменения статуса заказа.
    
    Содержит полный snapshot заказа + старый статус.
    """
    order_id: str
    user_id: int
    customer_name: str
    phone: str
    delivery: DeliveryMethod
    total: Decimal
    address: str | None
    comment: str | None
    old_status: OrderStatus
    new_status: OrderStatus
    status_comment: str | None
    created_at: datetime
    items: list[OrderEventItem] = field(default_factory=list)
    
    def to_payload(self) -> dict[str, Any]:
        """Сериализация в JSON-совместимый dict."""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "delivery": self.delivery,
            "total": str(self.total),
            "address": self.address,
            "comment": self.comment,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "status_comment": self.status_comment,
            "created_at": self.created_at.isoformat(),
            "items": [
                {
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "total": str(item.total),
                    "product_name": item.product_name,
                    "variant_weight": item.variant_weight,
                }
                for item in self.items
            ]
        }
    
    @classmethod
    def from_order(
        cls,
        order: OrderEntity,
        user_id: int,
        old_status: OrderStatus,
        status_comment: str | None = None
    ) -> "OrderStatusChangedEvent":
        """Создать событие из OrderEntity."""
        return cls(
            order_id=order.id,
            user_id=user_id,
            customer_name=order.customer_name,
            phone=order.phone,
            delivery=order.delivery,
            total=order.total,
            address=order.address,
            comment=order.comment,
            old_status=old_status,
            new_status=order.status,
            status_comment=status_comment,
            created_at=order.created_at or datetime.utcnow(),
            items=[
                OrderEventItem(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    product_name=item.product_name,
                    variant_weight=item.variant_weight,
                )
                for item in order.items
            ]
        )
