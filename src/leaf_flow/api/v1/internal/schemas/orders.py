from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel

from leaf_flow.api.v1.app.schemas.cart import CartItem

DeliveryMethod = Literal["pickup", "courier", "cdek"]
OrderStatus = Literal["created", "processing", "paid", "fulfilled", "cancelled"]

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
