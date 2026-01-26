from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import uow_dep, get_current_user
from leaf_flow.api.v1.auth.schemas.auth import (
    AuthResponse,
    AuthTokens,
    UserProfile,
    ErrorResponse,
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
    SetEmailRequest,
    RefreshRequest
)
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.auth_service import (
    refresh_tokens,
    register_email_user,
    authenticate_email_user,
    update_user_profile,
    change_user_password,
    set_user_email
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/refresh",
    response_model=AuthTokens,
    responses={
        401: {"model": ErrorResponse}
    }
)
async def refresh(payload: RefreshRequest, uow: UoW = Depends(uow_dep)) -> AuthTokens:
    refresh_token = payload.refreshToken
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refreshToken is required")
    try:
        tokens = await refresh_tokens(refresh_token, uow)
        return AuthTokens.model_validate(tokens, from_attributes=True)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.post(
    "/register",
    response_model=AuthResponse,
    responses={
        400: {"model": ErrorResponse}
    }
)
async def register(payload: RegisterRequest, uow: UoW = Depends(uow_dep)) -> AuthResponse:
    """
    Регистрация нового пользователя по email и паролю.
    """
    try:
        tokens, user = await register_email_user(
            email=str(payload.email),
            password=payload.password,
            first_name=payload.firstName,
            last_name=payload.lastName,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    
    return AuthResponse(
        tokens=AuthTokens.model_validate(tokens, from_attributes=True),
        user=UserProfile(
            id=str(user.id),
            telegramId=user.telegram_id,
            email=user.email,
            firstName=user.first_name,
            lastName=user.last_name,
            username=user.username,
            languageCode=user.language_code,
            photoUrl=user.photo_url,
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse}}
)
async def login(payload: LoginRequest, uow: UoW = Depends(uow_dep)) -> AuthResponse:
    """
    Авторизация пользователя по email и паролю.
    """
    try:
        tokens, user = await authenticate_email_user(
            email=str(payload.email),
            password=payload.password,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "INVALID_CREDENTIALS":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)
    
    return AuthResponse(
        tokens=AuthTokens.model_validate(tokens, from_attributes=True),
        user=UserProfile(
            id=str(user.id),
            telegramId=user.telegram_id,
            email=user.email,
            firstName=user.first_name,
            lastName=user.last_name,
            username=user.username,
            languageCode=user.language_code,
            photoUrl=user.photo_url,
        ),
    )


@router.get(
    "/profile",
    response_model=UserProfile,
    responses={401: {"model": ErrorResponse}}
)
async def profile(user: UserEntity = Depends(get_current_user)) -> UserProfile:
    return UserProfile(
        id=str(user.id),
        telegramId=user.telegram_id,
        email=user.email,
        firstName=user.first_name,
        lastName=user.last_name,
        username=user.username,
        languageCode=user.language_code,
        photoUrl=user.photo_url,
    )


@router.patch(
    "/profile",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def update_profile(
    payload: UpdateProfileRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> UserProfile:
    """
    Обновляет профиль пользователя (имя, фамилия, email).
    
    Передавайте только те поля, которые нужно изменить.
    """
    try:
        updated_user = await update_user_profile(
            current_user_id=user.id,
            first_name=payload.firstName,
            last_name=payload.lastName,
            email=payload.email,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    
    return UserProfile(
        id=str(updated_user.id),
        telegramId=updated_user.telegram_id,
        email=updated_user.email,
        firstName=updated_user.first_name,
        lastName=updated_user.last_name,
        username=updated_user.username,
        languageCode=updated_user.language_code,
        photoUrl=updated_user.photo_url,
    )


@router.post(
    "/password",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def change_password(
    payload: ChangePasswordRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> UserProfile:
    """
    Изменяет или создаёт пароль пользователя.
    
    - Если пароль уже установлен, требуется currentPassword
    - Если пароля нет (Telegram-пользователь), currentPassword не нужен
    """
    try:
        updated_user = await change_user_password(
            current_user_id=user.id,
            current_password=payload.currentPassword,
            new_password=payload.newPassword,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "CURRENT_PASSWORD_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для изменения пароля необходимо указать текущий пароль"
            )
        if error_message == "INVALID_CURRENT_PASSWORD":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный текущий пароль"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    
    return UserProfile(
        id=str(updated_user.id),
        telegramId=updated_user.telegram_id,
        email=updated_user.email,
        firstName=updated_user.first_name,
        lastName=updated_user.last_name,
        username=updated_user.username,
        languageCode=updated_user.language_code,
        photoUrl=updated_user.photo_url,
    )


@router.post(
    "/email",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def set_email(
    payload: SetEmailRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> UserProfile:
    """
    Устанавливает email и пароль для пользователя без email (Telegram-пользователь).
    
    После установки email пользователь сможет входить как через Telegram, так и по email/паролю.
    """
    try:
        updated_user = await set_user_email(
            current_user_id=user.id,
            email=str(payload.email),
            password=payload.password,
            uow=uow,
        )
    except ValueError as e:
        error_message = str(e)
        if error_message == "EMAIL_ALREADY_SET":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже установлен. Используйте PATCH /profile для изменения email"
            )
        if error_message == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    
    return UserProfile(
        id=str(updated_user.id),
        telegramId=updated_user.telegram_id,
        email=updated_user.email,
        firstName=updated_user.first_name,
        lastName=updated_user.last_name,
        username=updated_user.username,
        languageCode=updated_user.language_code,
        photoUrl=updated_user.photo_url,
    )
