from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence


@dataclass(slots=True)
class CartItemEntity:
    product_id: str
    variant_id: str
    quantity: int
    price: Decimal
    product_name: str | None = None
    variant_weight: str | None = None
    image: str | None = None

    @property
    def total(self) -> Decimal:
        return (self.price or Decimal("0.00")) * self.quantity


@dataclass(slots=True)
class CartEntity:
    items: Sequence[CartItemEntity]
    total_count: int
    total_price: Decimal


