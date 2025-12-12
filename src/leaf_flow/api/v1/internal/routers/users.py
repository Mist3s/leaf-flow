from fastapi import APIRouter, Depends, HTTPException, Path, status

from leaf_flow.api.deps import uow_dep, require_internal_auth
from leaf_flow.api.v1.internal.schemas.users import InternalUserPublic
from leaf_flow.infrastructure.db.uow import UoW


router = APIRouter()


@router.get("/by-telegram/{telegram_id}", response_model=InternalUserPublic, responses={404: {"description": "Not Found"}})
async def get_by_telegram_id(
    telegram_id: int = Path(...),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> InternalUserPublic:
    user = await uow.users.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь ещё не авторизовывался через WebApp",
        )
    return InternalUserPublic(
        id=str(user.id),
        telegramId=user.telegram_id,
        firstName=user.first_name,
        lastName=user.last_name,
        username=user.username,
        languageCode=user.language_code,
        photoUrl=user.photo_url,
    )


