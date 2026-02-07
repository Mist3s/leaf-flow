"""Схемы для вариантов продуктов в Admin API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class VariantDetail(BaseModel):
    id: str
    product_id: str | None = None
    weight: str
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class VariantCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    weight: str = Field(..., min_length=1, max_length=64)
    price: Decimal = Field(..., gt=0)
    is_active: bool = True
    sort_order: int = 0


class VariantUpdate(BaseModel):
    weight: str | None = None
    price: Decimal | None = None
    is_active: bool | None = None
    sort_order: int | None = None
