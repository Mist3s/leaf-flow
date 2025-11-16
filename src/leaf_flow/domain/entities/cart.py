from dataclasses import dataclass
from decimal import Decimal
from typing import List


@dataclass(slots=True)
class CartItemEntity:
    product_id: str
    variant_id: str
    quantity: int
    price: Decimal

    @property
    def total(self) -> Decimal:
        return (self.price or Decimal("0.00")) * self.quantity


@dataclass(slots=True)
class CartEntity:
    items: List[CartItemEntity]
    total_count: int
    total_price: Decimal


