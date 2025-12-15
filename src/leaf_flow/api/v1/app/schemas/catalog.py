from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import List


ProductCategory = str


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
    description: str
    category: ProductCategory
    tags: List[str]
    image: str
    variants: List[ProductVariant]
    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    items: List[Category]


class ProductListResponse(BaseModel):
    total: int
    items: List[Product]
