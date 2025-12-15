from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from leaf_flow.api.v1.app.routers.users import router as users_router
from leaf_flow.api.v1.auth.routers.auth import router as auth_router
from leaf_flow.api.v1.app.routers.catalog import router as catalog_router
from leaf_flow.api.v1.app.routers.cart import router as cart_router
from leaf_flow.api.v1.app.routers.orders import router as orders_router
from leaf_flow.api.v1.internal.routers.users import router as internal_users_router
from leaf_flow.api.v1.internal.routers.orders import router as internal_orders_router
from leaf_flow.api.v1.internal.routers.support_topics import router as internal_support_topics_router


def create_app() -> FastAPI:
    app = FastAPI(
        root_path="/api",
        title="leaf-flow",
        version="2.0.0"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(users_router, prefix="/v1/users", tags=["users"])
    app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])
    app.include_router(catalog_router, prefix="/v1/catalog", tags=["catalog"])
    app.include_router(cart_router, prefix="/v1/cart", tags=["cart"])
    app.include_router(orders_router, prefix="/v1/orders", tags=["orders"])
    app.include_router(internal_users_router, prefix="/v1/internal/users", tags=["internal"])
    app.include_router(internal_orders_router, prefix="/v1/internal/orders", tags=["internal"])
    app.include_router(internal_support_topics_router, prefix="/v1/internal/support-topics", tags=["internal"])
    return app


app = create_app()
