from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

DeliveryMethod = Literal["pickup", "courier", "cdek"]
OrderStatus = Literal["created", "processing", "paid", "fulfilled", "cancelled"]


class CartItem(BaseModel):
    price: Decimal
    total: Decimal
    productId: str
    variantId: str
    quantity: int = Field(1, ge=1)


class InternalOrderListItem(BaseModel):
    orderId: str
    customerName: str
    deliveryMethod: DeliveryMethod
    total: Decimal
    status: OrderStatus
    createdAt: datetime


class InternalOrderListResponse(BaseModel):
    items: list[InternalOrderListItem]


class UpdateOrderStatusRequest(BaseModel):
    newStatus: OrderStatus
    comment: str | None = None


class InternalCartItem(CartItem):
    """Расширенная схема CartItem с названиями продукта и варианта"""
    productName: str
    variantWeight: str


class InternalOrderDetails(BaseModel):
    """Расширенная схема OrderDetails с названиями продуктов и вариантов"""
    orderId: str
    customerName: str
    deliveryMethod: DeliveryMethod
    total: Decimal
    items: list[InternalCartItem]
    address: str | None = None
    comment: str | None = None
    status: OrderStatus
    createdAt: datetime
