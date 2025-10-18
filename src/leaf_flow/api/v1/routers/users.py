from fastapi import APIRouter, Depends

from leaf_flow.api.v1.schemas.users import UserCreate, UserRead
from leaf_flow.api.deps import uow_dep
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.user_service import create_user

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=201)
async def create(payload: UserCreate, uow: UoW = Depends(uow_dep)) -> UserRead:
    user = await create_user(str(payload.email), payload.name, uow)
    return UserRead.model_validate(user)
