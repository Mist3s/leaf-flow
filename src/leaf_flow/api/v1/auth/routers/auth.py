from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import uow_dep, get_current_user
from leaf_flow.api.v1.auth.schemas.auth import (
    TelegramInitRequest,
    AuthResponse,
    AuthTokens,
    UserProfile,
    ErrorResponse,
    RegisterRequest,
    LoginRequest,
)
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.auth_service import (
    exchange_init_data_for_tokens,
    refresh_tokens,
    register_email_user,
    authenticate_email_user,
)


router = APIRouter()


@router.post("/telegram/init", response_model=AuthResponse, responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}})
async def telegram_init(payload: TelegramInitRequest, uow: UoW = Depends(uow_dep)) -> AuthResponse:
    try:
        tokens, user = await exchange_init_data_for_tokens(payload.initData, uow)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    resp = AuthResponse(
        tokens=AuthTokens.model_validate(tokens.model_dump()),
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
    return resp


@router.post("/refresh", response_model=AuthTokens, responses={401: {"model": ErrorResponse}})
async def refresh(payload: dict, uow: UoW = Depends(uow_dep)) -> AuthTokens:
    refresh_token = payload.get("refreshToken")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refreshToken is required")
    try:
        tokens = await refresh_tokens(refresh_token, uow)
        return AuthTokens.model_validate(tokens.model_dump())
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.post("/register", response_model=AuthResponse, responses={400: {"model": ErrorResponse}})
async def register(payload: RegisterRequest, uow: UoW = Depends(uow_dep)) -> AuthResponse:
    """
    Регистрация нового пользователя по email и паролю.
    """
    try:
        tokens, user = await register_email_user(
            email=payload.email,
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
        tokens=AuthTokens.model_validate(tokens.model_dump()),
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


@router.post("/login", response_model=AuthResponse, responses={401: {"model": ErrorResponse}})
async def login(payload: LoginRequest, uow: UoW = Depends(uow_dep)) -> AuthResponse:
    """
    Авторизация пользователя по email и паролю.
    """
    try:
        tokens, user = await authenticate_email_user(
            email=payload.email,
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
        tokens=AuthTokens.model_validate(tokens.model_dump()),
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


@router.get("/profile", response_model=UserProfile, responses={401: {"model": ErrorResponse}})
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


