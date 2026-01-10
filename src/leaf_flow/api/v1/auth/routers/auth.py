from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import uow_dep, get_current_user
from leaf_flow.api.v1.auth.schemas.auth import (
    TelegramInitRequest,
    TelegramLoginWidgetRequest,
    AuthResponse,
    AuthTokens,
    UserProfile,
    ErrorResponse,
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
    SetEmailRequest,
)
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.auth_service import (
    exchange_init_data_for_tokens,
    exchange_login_widget_for_tokens,
    link_telegram_to_user,
    merge_telegram_account,
    unlink_telegram_from_user,
    refresh_tokens,
    register_email_user,
    authenticate_email_user,
    update_user_profile,
    change_user_password,
    set_user_email,
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


@router.post("/telegram/login-widget", response_model=AuthResponse, responses={400: {"model": ErrorResponse}})
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
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


@router.post("/telegram/link", response_model=UserProfile, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
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
                detail="Этот Telegram-аккаунт уже привязан к другому пользователю. Используйте /telegram/merge для слияния аккаунтов."
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


@router.post("/telegram/merge", response_model=UserProfile, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
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


@router.delete("/telegram/link", response_model=UserProfile, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
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


@router.patch("/profile", response_model=UserProfile, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
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


@router.post("/password", response_model=UserProfile, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
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


@router.post("/email", response_model=UserProfile, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
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
            email=payload.email,
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


