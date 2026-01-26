from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import uow_dep, get_current_user
from leaf_flow.api.v1.auth.schemas.auth import (
    AuthResponse,
    AuthTokens,
    UserProfile,
    ErrorResponse
)
from leaf_flow.api.v1.auth.schemas.telegram import (
    TelegramInitRequest,
    TelegramLoginWidgetRequest
)
from leaf_flow.application.auth.exceptions import InvalidInitData, InvalidWidgetData
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.auth_service import (
    exchange_init_data_for_tokens,
    exchange_login_widget_for_tokens,
    link_telegram_to_user,
    merge_telegram_account,
    unlink_telegram_from_user
)


router = APIRouter(prefix="/auth/telegram", tags=["telegram"])


@router.post(
    "/init",
    response_model=AuthResponse,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse}
    }
)
async def telegram_init(
    payload: TelegramInitRequest,
    uow: UoW = Depends(uow_dep)
) -> AuthResponse:
    try:
        tokens, user = await exchange_init_data_for_tokens(payload.initData, uow)
    except InvalidInitData as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    resp = AuthResponse(
        tokens=AuthTokens.model_validate(tokens, from_attributes=True),
        user=UserProfile.model_validate(user, from_attributes=True)
    )
    return resp


@router.post(
    "/login-widget",
    response_model=AuthResponse,
    responses={400: {"model": ErrorResponse}}
)
async def telegram_login_widget(
    payload: TelegramLoginWidgetRequest,
    uow: UoW = Depends(uow_dep)
) -> AuthResponse:
    """
    Авторизация через Telegram Login Widget.

    Принимает payload от виджета, валидирует подпись,
    создаёт или находит пользователя и возвращает токены.
    """
    try:
        tokens, user = await exchange_login_widget_for_tokens(
            widget_data=payload.model_dump(),
            uow=uow,
        )
    except InvalidWidgetData as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AuthResponse(
        tokens=AuthTokens.model_validate(tokens, from_attributes=True),
        user=UserProfile.model_validate(user, from_attributes=True),
    )


@router.post(
    "/link",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        409: {"model": ErrorResponse}
    }
)
async def telegram_link(
    payload: TelegramLoginWidgetRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> UserProfile:
    """
    Привязывает Telegram-аккаунт к текущему пользователю.

    Если telegram_id уже привязан к другому аккаунту, возвращает ошибку 409 Conflict.
    Для слияния аккаунтов используйте POST /telegram/merge.
    """
    try:
        updated_user = await link_telegram_to_user(
            widget_data=payload.model_dump(),
            current_user_id=user.id,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "TELEGRAM_ALREADY_LINKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram уже привязан к вашему аккаунту"
            )
        if error_message == "TELEGRAM_LINKED_TO_ANOTHER_ACCOUNT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Этот Telegram-аккаунт уже привязан к другому пользователю. "
                    "Используйте /telegram/merge для слияния аккаунтов."
                )
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    except InvalidWidgetData as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return UserProfile.model_validate(updated_user, from_attributes=True)


@router.post(
    "/merge",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def telegram_merge(
    payload: TelegramLoginWidgetRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> UserProfile:
    """
    Выполняет слияние аккаунтов: привязывает Telegram к текущему пользователю,
    перенося данные со старого Telegram-аккаунта.

    При слиянии:
    - Заказы переносятся на текущего пользователя
    - Корзина старого аккаунта удаляется
    - Старый аккаунт удаляется

    Используйте этот эндпоинт после получения ошибки 409 от POST /telegram/link.
    """
    try:
        updated_user = await merge_telegram_account(
            widget_data=payload.model_dump(),
            current_user_id=user.id,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "TELEGRAM_ALREADY_LINKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram уже привязан к вашему аккаунту"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    return UserProfile.model_validate(updated_user, from_attributes=True)


@router.delete(
    "/link",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def telegram_unlink(
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> UserProfile:
    """
    Отвязывает Telegram от аккаунта пользователя.

    Отвязка возможна только если у пользователя есть email и пароль.
    """
    try:
        updated_user = await unlink_telegram_from_user(
            current_user_id=user.id,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "TELEGRAM_NOT_LINKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram не привязан к аккаунту"
            )
        if error_message == "CANNOT_UNLINK_NO_EMAIL_PASSWORD":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно отвязать Telegram: необходимо сначала привязать email и установить пароль"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    return UserProfile.model_validate(updated_user, from_attributes=True)
