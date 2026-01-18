from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional


DeliveryMethod = Literal["pickup", "courier", "cdek"]
OrderStatus = Literal["created", "processing", "paid", "fulfilled", "cancelled"]


@dataclass(slots=True)
class OrderItemEntity:
    product_id: str
    variant_id: str
    quantity: int
    price: Decimal
    total: Decimal
    product_name: str
    variant_weight: str
    image: str


@dataclass(slots=True)
class OrderEntity:
    id: str
    customer_name: str
    phone: str
    user_id: int
    delivery: DeliveryMethod
    total: Decimal
    items: List[OrderItemEntity]
    address: Optional[str] = None
    comment: Optional[str] = None
    status: OrderStatus = "created"
    created_at: Optional[datetime] = None
