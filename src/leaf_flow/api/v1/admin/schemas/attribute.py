"""Схемы для атрибутов продуктов в Admin API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


AttributeKind = Literal["single", "multi", "bool", "range"]
UIHint = Literal["chips", "radio", "toggle", "scale"]


class AttributeValueDetail(BaseModel):
    id: int
    attribute_id: int
    name: str
    slug: str
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AttributeDetail(BaseModel):
    id: int
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool
    created_at: datetime
    kind: AttributeKind
    ui_hint: UIHint
    values: list[AttributeValueDetail]

    model_config = ConfigDict(from_attributes=True)


class ProductAttributeValuesUpdate(BaseModel):
    attribute_value_ids: list[int]
