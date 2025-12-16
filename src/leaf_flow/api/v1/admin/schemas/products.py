from __future__ import annotations

from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from leaf_flow.api.v1.app.schemas.catalog import Product, ProductVariant


class ProductCreateRequest(BaseModel):
    id: str = Field(..., description="Product identifier")
    name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    image: str | None = None
    image_base64: str | None = None
    variants: List["ProductVariantCreateRequest"] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: List[str] | None = None
    image: str | None = None
    image_base64: str | None = None
    variants: List["ProductVariantCreateRequest"] | None = None

    model_config = ConfigDict(extra="forbid")


class ProductVariantCreateRequest(BaseModel):
    id: str
    weight: str
    price: Decimal

    model_config = ConfigDict(extra="forbid")


class ProductVariantUpdateRequest(BaseModel):
    weight: str | None = None
    price: Decimal | None = None

    model_config = ConfigDict(extra="forbid")


class AdminProductResponse(Product):
    model_config = ConfigDict(from_attributes=True)


class AdminProductVariantResponse(ProductVariant):
    model_config = ConfigDict(from_attributes=True)


ProductCreateRequest.model_rebuild()
ProductUpdateRequest.model_rebuild()
