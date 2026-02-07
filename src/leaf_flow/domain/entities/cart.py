from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Sequence, List

from leaf_flow.domain.entities.product import ProductImageEntity


@dataclass(slots=True)
class CartItemEntity:
    product_id: str
    variant_id: str
    quantity: int
    price: Decimal
    product_name: str | None = None
    variant_weight: str | None = None
    image: str | None = None
    images: List[ProductImageEntity] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return (self.price or Decimal("0.00")) * self.quantity


@dataclass(slots=True)
class CartEntity:
    id: int
    user_id: int
    updated_at: datetime


@dataclass(slots=True)
class CartDetailEntity:
    items: Sequence[CartItemEntity]
    total_count: int
    total_price: Decimal
