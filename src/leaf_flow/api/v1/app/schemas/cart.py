from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List


class CartItemInput(BaseModel):
    productId: str
    variantId: str
    quantity: int = Field(1, ge=1)


class CartItem(CartItemInput):
    price: Decimal
    total: Decimal


class Cart(BaseModel):
    items: List[CartItem]
    totalCount: int
    totalPrice: Decimal
    updatedAt: datetime | None = None
