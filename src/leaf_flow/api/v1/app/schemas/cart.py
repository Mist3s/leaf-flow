from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from typing import List


class CartItemInput(BaseModel):
    productId: str
    variantId: str
    quantity: int = Field(1, ge=1)


class CartItem(BaseModel):
    productId: str = Field(validation_alias="product_id")
    variantId: str = Field(validation_alias="variant_id")
    quantity: int = Field(1, ge=1)
    productName: str = Field(validation_alias="product_name")
    variantWeight: str = Field(validation_alias="variant_weight")
    image: str
    price: Decimal
    total: Decimal


class CartSchema(BaseModel):
    items: List[CartItem]
    totalCount: int = Field(validation_alias="total_count")
    totalPrice: Decimal = Field(validation_alias="total_price")
    updatedAt: datetime | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
