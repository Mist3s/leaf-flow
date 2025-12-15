from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from leaf_flow.api.v1.app.schemas.catalog import ProductVariant, Product


class ProductCreateRequest(BaseModel):
    id: str = Field(..., description="Product identifier")
    name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    image: str


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: List[str] | None = None
    image: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProductVariantCreateRequest(BaseModel):
    id: str
    weight: str
    price: Decimal


class ProductVariantUpdateRequest(BaseModel):
    weight: str | None = None
    price: Decimal | None = None

    model_config = ConfigDict(extra="forbid")


class AdminProductResponse(Product):
    model_config = ConfigDict(from_attributes=True)


class AdminProductVariantResponse(ProductVariant):
    model_config = ConfigDict(from_attributes=True)
