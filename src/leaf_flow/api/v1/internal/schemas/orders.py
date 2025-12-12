from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class InternalOrderListItem(BaseModel):
    orderId: str
    customerName: str
    deliveryMethod: str
    total: Decimal
    status: str
    createdAt: datetime


class InternalOrderListResponse(BaseModel):
    items: list[InternalOrderListItem]
