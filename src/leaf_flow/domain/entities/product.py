from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Literal


AttributeKind = Literal["single", "multi", "bool", "range"]
UIHint = Literal["chips", "radio", "toggle", "scale"]


@dataclass(slots=True)
class ProductVariantEntity:
    id: str
    weight: str
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int


@dataclass(slots=True)
class ProductAttributesValue:
    id: int
    attribute_id: int
    name: str
    slug: str
    sort_order: int
    is_active: bool


@dataclass(slots=True)
class ProductAttributes:
    id: int
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool
    created_at: datetime
    kind: AttributeKind
    ui_hint: UIHint
    values: List[ProductAttributesValue]


@dataclass(slots=True)
class BrewProfileEntity:
    id: int
    method: str
    teaware: str
    temperature: str
    brew_time: str
    note: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ProductEntity:
    id: str
    name: str
    description: str
    category_slug: str
    image: str
    product_type_code: str
    tags: List[str]
    variants: List[ProductVariantEntity]
    brew_profiles: list[BrewProfileEntity]
    attribute_values: List[ProductAttributes]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sort_order: int
