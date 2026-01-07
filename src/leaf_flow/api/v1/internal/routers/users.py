from fastapi import APIRouter, Depends, HTTPException, Path, status

from leaf_flow.api.deps import uow_dep, require_internal_auth
from leaf_flow.api.v1.internal.schemas.users import InternalUserPublic, TelegramBotRegisterRequest
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.auth_service import register_user_from_bot


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
    # В этом эндпоинте telegram_id всегда присутствует, т.к. мы ищем по telegram_id
    # Но для безопасности проверяем
    if user.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User data inconsistency",
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


@router.post("/register", response_model=InternalUserPublic, status_code=201, responses={400: {"description": "Bad Request"}})
async def register_user(
    payload: TelegramBotRegisterRequest,
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> InternalUserPublic:
    """
    Регистрация пользователя из Telegram бота без верификации initData.
    Бот передает данные пользователя напрямую.
    Требует авторизации через INTERNAL_BOT_TOKEN.
    Токены не генерируются.
    """
    try:
        user = await register_user_from_bot(
            telegram_id=payload.telegramId,
            first_name=payload.firstName,
            last_name=payload.lastName,
            username=payload.username,
            language_code=payload.languageCode,
            photo_url=payload.photoUrl,
            uow=uow,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    # После регистрации через register_user_from_bot telegram_id всегда присутствует
    # Но для безопасности проверяем
    if user.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User data inconsistency",
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


