from datetime import datetime
from decimal import Decimal
from typing import List, Literal
from pydantic import BaseModel, Field

from leaf_flow.api.v1.app.schemas.cart import CartItem


DeliveryMethod = Literal["pickup", "courier", "cdek"]
OrderStatus = Literal["created", "processing", "paid", "fulfilled", "cancelled"]


class OrderRequest(BaseModel):
    customerName: str = Field(min_length=1)
    phone: str
    delivery: DeliveryMethod
    address: str | None = None
    comment: str | None = Field(default=None, max_length=500)
    expectedTotal: Decimal | None = None


class OrderSummary(BaseModel):
    orderId: str
    customerName: str
    deliveryMethod: str
    total: Decimal


class OrderDetails(OrderSummary):
    items: List[CartItem]
    address: str | None = None
    comment: str | None = None
    status: OrderStatus
    createdAt: datetime


