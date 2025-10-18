from fastapi import FastAPI

from leaf_flow.api.v1.routers.users import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="leaf-flow")
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    return app


app = create_app()
