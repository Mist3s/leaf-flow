from fastapi import FastAPI

from leaf_flow.api.v1.app.routers.users import router as users_router
from leaf_flow.api.v1.auth.routers.auth import router as auth_router
from leaf_flow.api.v1.app.routers.catalog import router as catalog_router
from leaf_flow.api.v1.app.routers.cart import router as cart_router
from leaf_flow.api.v1.app.routers.orders import router as orders_router
from leaf_flow.infrastructure.db.base import Base


def create_app() -> FastAPI:
    app = FastAPI(title="leaf-flow")
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["catalog"])
    app.include_router(cart_router, prefix="/api/v1/cart", tags=["cart"])
    app.include_router(orders_router, prefix="/api/v1/orders", tags=["orders"])
    return app


app = create_app()
print(Base.metadata.tables.keys())
