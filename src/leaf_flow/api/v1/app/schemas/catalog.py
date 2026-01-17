from datetime import datetime
from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field

AttributeKind = Literal["single", "multi", "bool", "range"]
UIHint = Literal["chips", "radio", "toggle", "scale"]
ProductCategory = str


class BrewProfileOut(BaseModel):
    id: int
    method: str
    teaware: str
    temperature: str
    brew_time: str
    weight: str
    note: str
    note: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductVariantOut(BaseModel):
    id: str
    weight: str
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ProductAttributeValueOut(BaseModel):
    id: int
    attribute_id: int
    name: str
    slug: str
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProductAttributeOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool
    created_at: datetime
    kind: AttributeKind
    ui_hint: UIHint
    values: List[ProductAttributeValueOut]

    model_config = ConfigDict(from_attributes=True)


class ProductDetail(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory = Field(validation_alias="category_slug")
    tags: List[str]
    image: str
    variants: List[ProductVariantOut]
    product_type_code: str
    attributes: List[ProductAttributeOut] = Field(validation_alias="attribute_values")
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int
    brewing_profiles: List[BrewProfileOut] = Field(validation_alias="brew_profiles")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Category(BaseModel):
    id: ProductCategory
    label: str


class ProductVariant(BaseModel):
    id: str
    weight: str
    price: Decimal
    model_config = ConfigDict(from_attributes=True)


class Product(BaseModel):
    id: str
    name: str
    category: ProductCategory = Field(validation_alias="category_slug")
    tags: List[str]
    product_type_code: str
    image: str
    variants: List[ProductVariant]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CategoryListResponse(BaseModel):
    items: List[Category]


class ProductListResponse(BaseModel):
    total: int
    items: List[Product]
