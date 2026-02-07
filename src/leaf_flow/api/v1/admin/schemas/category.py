"""Схемы для категорий в Admin API."""

from pydantic import BaseModel, ConfigDict, Field


class CategoryDetail(BaseModel):
    slug: str
    label: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=255)
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    label: str | None = None
    sort_order: int | None = None
