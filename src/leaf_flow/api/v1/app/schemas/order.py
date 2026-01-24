from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field



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
    deliveryMethod: DeliveryMethod
    total: Decimal


class OrderListItem(BaseModel):
    orderId: str
    customerName: str
    deliveryMethod: DeliveryMethod
    total: Decimal
    status: OrderStatus
    createdAt: datetime


class OrderItemDetails(BaseModel):
    productId: str
    variantId: str
    quantity: int
    price: Decimal
    total: Decimal
    productName: str
    variantWeight: str


class OrderDetails(OrderSummary):
    items: list[OrderItemDetails]
    address: str | None = None
    comment: str | None = None
    status: OrderStatus
    createdAt: datetime


