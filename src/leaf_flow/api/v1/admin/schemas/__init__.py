"""Pydantic схемы для Admin API."""

from leaf_flow.api.v1.admin.schemas.image import ProductImage, ProductImageVariant
from leaf_flow.api.v1.admin.schemas.product import (
    ProductCreate,
    ProductDetail,
    ProductList,
    ProductUpdate,
    SuccessResponse,
    SuccessWithAddedResponse,
)
from leaf_flow.api.v1.admin.schemas.variant import (
    VariantCreate,
    VariantDetail,
    VariantUpdate,
)
from leaf_flow.api.v1.admin.schemas.brew_profile import (
    BrewProfileCreate,
    BrewProfileDetail,
    BrewProfileUpdate,
)
from leaf_flow.api.v1.admin.schemas.category import (
    CategoryCreate,
    CategoryDetail,
    CategoryUpdate,
)
from leaf_flow.api.v1.admin.schemas.order import (
    OrderDetail,
    OrderItemDetail,
    OrderItemsUpdate,
    OrderItemUpdate,
    OrderList,
    OrderStatusUpdate,
    OrderUpdate,
)
from leaf_flow.api.v1.admin.schemas.review import (
    ReviewCreate,
    ReviewDetail,
    ReviewList,
    ReviewUpdate,
)
from leaf_flow.api.v1.admin.schemas.user import (
    UserDetail,
    UserList,
    UserUpdate,
)
from leaf_flow.api.v1.admin.schemas.attribute import (
    AttributeDetail,
    AttributeValueDetail,
    ProductAttributeValuesUpdate,
)

__all__ = [
    "ProductImage",
    "ProductImageVariant",
    "ProductCreate",
    "ProductDetail",
    "ProductList",
    "ProductUpdate",
    "SuccessResponse",
    "SuccessWithAddedResponse",
    "VariantCreate",
    "VariantDetail",
    "VariantUpdate",
    "BrewProfileCreate",
    "BrewProfileDetail",
    "BrewProfileUpdate",
    "CategoryCreate",
    "CategoryDetail",
    "CategoryUpdate",
    "OrderDetail",
    "OrderItemDetail",
    "OrderItemsUpdate",
    "OrderItemUpdate",
    "OrderList",
    "OrderStatusUpdate",
    "OrderUpdate",
    "ReviewCreate",
    "ReviewDetail",
    "ReviewList",
    "ReviewUpdate",
    "UserDetail",
    "UserList",
    "UserUpdate",
    "AttributeDetail",
    "AttributeValueDetail",
    "ProductAttributeValuesUpdate",
]
