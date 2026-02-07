"""Роутеры Admin API."""

from leaf_flow.api.v1.admin.routers.image import router as catalog_router
from leaf_flow.api.v1.admin.routers.products import router as products_router
from leaf_flow.api.v1.admin.routers.categories import router as categories_router
from leaf_flow.api.v1.admin.routers.orders import router as orders_router
from leaf_flow.api.v1.admin.routers.reviews import router as reviews_router
from leaf_flow.api.v1.admin.routers.users import router as users_router

__all__ = [
    "catalog_router",
    "products_router",
    "categories_router",
    "orders_router",
    "reviews_router",
    "users_router",
]
