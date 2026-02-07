"""Схемы для профилей заваривания в Admin API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BrewProfileDetail(BaseModel):
    id: int
    product_id: str | None = None
    method: str
    teaware: str
    temperature: str
    brew_time: str
    weight: str
    note: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrewProfileCreate(BaseModel):
    method: str = Field(..., min_length=1, max_length=64)
    teaware: str = Field(..., min_length=1, max_length=128)
    temperature: str = Field(..., min_length=1, max_length=64)
    brew_time: str = Field(..., min_length=1, max_length=64)
    weight: str = Field(..., min_length=1, max_length=64)
    note: str | None = None
    sort_order: int = 0
    is_active: bool = True


class BrewProfileUpdate(BaseModel):
    method: str | None = None
    teaware: str | None = None
    temperature: str | None = None
    brew_time: str | None = None
    weight: str | None = None
    note: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
