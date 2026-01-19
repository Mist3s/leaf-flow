from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis.asyncio import Redis

from leaf_flow.api.v1.auth.routers.auth import router as auth_router
from leaf_flow.api.v1.app.routers.catalog import router as catalog_router
from leaf_flow.api.v1.app.routers.cart import router as cart_router
from leaf_flow.api.v1.app.routers.orders import router as orders_router
from leaf_flow.api.v1.app.routers.reviews import router as reviews_router
from leaf_flow.api.v1.internal.routers.users import router as internal_users_router
from leaf_flow.api.v1.internal.routers.orders import router as internal_orders_router
from leaf_flow.api.v1.internal.routers.support_topics import router as internal_support_topics_router
from leaf_flow.api.v1.admin.routers.products import router as admin_products_router
from leaf_flow.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis: Redis | None = None
    try:
        redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            socket_timeout=5,
            socket_connect_timeout=5,
            health_check_interval=30,
            # decode_responses=True,
        )
        await redis.ping()
        app.state.redis = redis
        yield
    finally:
        if redis is not None:
            await redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        root_path="/api",
        title="leaf-flow",
        version="2.0.0",
        lifespan=lifespan
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_images_dir = Path(settings.IMAGES_DIR)
    app.mount("/images", StaticFiles(directory=static_images_dir), name="images")

    app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])
    app.include_router(catalog_router, prefix="/v1/catalog", tags=["catalog"])
    app.include_router(cart_router, prefix="/v1/cart", tags=["cart"])
    app.include_router(orders_router, prefix="/v1/orders", tags=["orders"])
    app.include_router(reviews_router, prefix="/v1/reviews", tags=["reviews"])
    app.include_router(admin_products_router, prefix="/v1/admin/products", tags=["admin-products"])
    app.include_router(internal_users_router, prefix="/v1/internal/users", tags=["internal"])
    app.include_router(internal_orders_router, prefix="/v1/internal/orders", tags=["internal"])
    app.include_router(internal_support_topics_router, prefix="/v1/internal/support-topics", tags=["internal"])
    return app


app = create_app()
