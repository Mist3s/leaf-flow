"""Схемы для заказов в Admin API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


OrderStatus = Literal["created", "processing", "paid", "fulfilled", "cancelled"]
DeliveryMethod = Literal["pickup", "courier", "cdek"]


class OrderItemDetail(BaseModel):
    product_id: str
    variant_id: str
    quantity: int
    price: Decimal
    total: Decimal
    product_name: str
    variant_weight: str
    image: str

    model_config = ConfigDict(from_attributes=True)


class OrderDetail(BaseModel):
    id: str
    customer_name: str
    phone: str
    user_id: int | None
    delivery: DeliveryMethod
    address: str | None
    comment: str | None
    total: Decimal
    status: OrderStatus
    created_at: datetime | None
    items: list[OrderItemDetail]

    model_config = ConfigDict(from_attributes=True)


class OrderList(BaseModel):
    total: int
    items: list[OrderDetail]


class OrderUpdate(BaseModel):
    customer_name: str | None = None
    phone: str | None = None
    delivery: DeliveryMethod | None = None
    address: str | None = None
    comment: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemUpdate(BaseModel):
    product_id: str
    variant_id: str
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)


class OrderItemsUpdate(BaseModel):
    items: list[OrderItemUpdate]
