from dataclasses import dataclass
from decimal import Decimal
from typing import List


@dataclass(slots=True)
class ProductVariantEntity:
    id: str
    weight: str
    price: Decimal


@dataclass(slots=True)
class ProductEntity:
    id: str
    name: str
    description: str
    category_slug: str
    tags: List[str]
    image: str
    variants: List[ProductVariantEntity]


