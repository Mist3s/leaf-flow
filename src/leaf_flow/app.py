from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis.asyncio import Redis

from leaf_flow.api.v1.auth.routers.auth import router as auth_router
from leaf_flow.api.v1.auth.routers.telegram import router as telegram_router
from leaf_flow.api.v1.app.routers.catalog import router as catalog_router
from leaf_flow.api.v1.app.routers.cart import router as cart_router
from leaf_flow.api.v1.app.routers.order import router as orders_router
from leaf_flow.api.v1.app.routers.review import router as reviews_router
from leaf_flow.api.v1.internal.routers.user import router as internal_users_router
from leaf_flow.api.v1.internal.routers.order import router as internal_orders_router
from leaf_flow.api.v1.internal.routers.support_topic import router as internal_support_topics_router
from leaf_flow.api.v1.admin.routers.image import router as admin_catalog_router
from leaf_flow.api.v1.admin.routers.products import router as admin_products_router
from leaf_flow.api.v1.admin.routers.categories import router as admin_categories_router
from leaf_flow.api.v1.admin.routers.orders import router as admin_orders_router
from leaf_flow.api.v1.admin.routers.reviews import router as admin_reviews_router
from leaf_flow.api.v1.admin.routers.users import router as admin_users_router
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

    api_v1 = APIRouter(prefix="/v1")

    api_v1.include_router(auth_router)
    api_v1.include_router(telegram_router)
    api_v1.include_router(catalog_router)
    api_v1.include_router(cart_router)
    api_v1.include_router(orders_router)
    api_v1.include_router(reviews_router)
    api_v1.include_router(internal_users_router)
    api_v1.include_router(internal_orders_router)
    api_v1.include_router(internal_support_topics_router)

    api_v1.include_router(admin_catalog_router)
    api_v1.include_router(admin_products_router)
    api_v1.include_router(admin_categories_router)
    api_v1.include_router(admin_orders_router)
    api_v1.include_router(admin_reviews_router)
    api_v1.include_router(admin_users_router)

    app.include_router(api_v1)
    return app


app = create_app()
