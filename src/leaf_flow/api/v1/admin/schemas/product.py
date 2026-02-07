"""Схемы для продуктов в Admin API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SuccessResponse(BaseModel):
    """Стандартный ответ для успешных операций."""

    success: bool = True


class SuccessWithAddedResponse(BaseModel):
    """Ответ для операций добавления."""

    success: bool = True
    added: bool


class VariantBrief(BaseModel):
    id: str
    weight: str
    price: Decimal
    is_active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class BrewProfileBrief(BaseModel):
    id: int
    method: str
    teaware: str
    temperature: str
    brew_time: str
    weight: str
    note: str | None
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


ImageVariant = Literal["original", "thumb", "md", "lg"]
ImageFormat = Literal["jpg", "jpeg", "png", "webp"]


class ProductImageVariantBrief(BaseModel):
    id: int
    variant: ImageVariant
    format: ImageFormat
    storage_key: str
    width: int
    height: int

    model_config = ConfigDict(from_attributes=True)


class ProductImageBrief(BaseModel):
    id: int
    title: str
    is_active: bool
    sort_order: int
    variants: list[ProductImageVariantBrief]

    model_config = ConfigDict(from_attributes=True)


class AttributeValueBrief(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class AttributeBrief(BaseModel):
    id: int
    code: str
    name: str
    values: list[AttributeValueBrief]

    model_config = ConfigDict(from_attributes=True)


class ProductDetail(BaseModel):
    id: str
    name: str
    description: str
    category_slug: str
    image: str
    product_type_code: str
    tags: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int
    variants: list[VariantBrief]
    brew_profiles: list[BrewProfileBrief]
    images: list[ProductImageBrief]
    attribute_values: list[AttributeBrief]

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    total: int
    items: list[ProductDetail]


class ProductCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    category_slug: str
    image: str = Field(default="")
    product_type_code: str
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    category_slug: str | None = Field(None, min_length=1, max_length=64)
    image: str | None = Field(None, max_length=500)
    product_type_code: str | None = Field(None, min_length=1, max_length=64)
    tags: list[str] | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(None, ge=0)
