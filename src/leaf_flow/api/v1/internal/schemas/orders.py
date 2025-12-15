from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel

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
