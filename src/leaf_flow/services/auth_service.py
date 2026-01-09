import json
from datetime import timedelta
from urllib.parse import parse_qsl

from pydantic import BaseModel

from leaf_flow.config import settings
from leaf_flow.infrastructure.db.models.tokens import RefreshToken
from leaf_flow.infrastructure.db.models.users import User
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.security import (
    verify_telegram_webapp_request,
    verify_telegram_login_widget,
    create_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
    _utcnow
)
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.domain.mappers import map_user_model_to_entity


class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    refreshExpiresIn: int


class TelegramProfile(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None


async def exchange_init_data_for_tokens(init_data: str, uow: UoW) -> tuple[AuthTokens, UserEntity]:
    if not verify_telegram_webapp_request(init_data, settings.TELEGRAM_BOT_TOKEN):
        raise ValueError("INVALID_INIT_DATA")

    data = dict(parse_qsl(init_data))
    user_json = data.get("user")

    if not user_json:
        raise ValueError("INVALID_INIT_DATA")

    tuser = TelegramProfile.model_validate(json.loads(user_json))
    user = await uow.users.get_by_telegram_id(tuser.id)

    if user is None:
        user = User(
            telegram_id=tuser.id,
            first_name=tuser.first_name,
            last_name=tuser.last_name,
            username=tuser.username,
            language_code=tuser.language_code,
            photo_url=tuser.photo_url,
        )
        await uow.users.add(user)
        await uow.flush()
    else:
        # Обновляем данные существующего пользователя
        user.first_name = tuser.first_name
        user.last_name = tuser.last_name
        user.username = tuser.username
        user.language_code = tuser.language_code
        user.photo_url = tuser.photo_url
        await uow.flush()

    # Генерируем токены
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in),
    )
    await uow.refresh_tokens.add(refresh)
    await uow.commit()

    tokens = AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_raw,
        expiresIn=access_ttl,
        refreshExpiresIn=refresh_expires_in,
    )
    return tokens, map_user_model_to_entity(user)


async def exchange_login_widget_for_tokens(
    widget_data: dict,
    uow: UoW
) -> tuple[AuthTokens, UserEntity]:
    """
    Авторизация через Telegram Login Widget.
    
    Валидирует данные от Login Widget, создаёт/находит пользователя
    и возвращает токены авторизации.
    
    Args:
        widget_data: Данные от Login Widget (id, first_name, auth_date, hash, ...)
        uow: Unit of Work
        
    Returns:
        Кортеж из токенов авторизации и сущности пользователя
        
    Raises:
        ValueError: Если данные невалидны или устарели
    """
    # Валидация подписи и auth_date
    if not verify_telegram_login_widget(widget_data, settings.TELEGRAM_BOT_TOKEN):
        raise ValueError("INVALID_LOGIN_WIDGET_DATA")
    
    telegram_id = widget_data["id"]
    first_name = widget_data["first_name"]
    last_name = widget_data.get("last_name")
    username = widget_data.get("username")
    photo_url = widget_data.get("photo_url")
    
    # Ищем или создаём пользователя
    user = await uow.users.get_by_telegram_id(telegram_id)
    
    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            photo_url=photo_url,
        )
        await uow.users.add(user)
        await uow.flush()
    else:
        # Обновляем данные существующего пользователя
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.photo_url = photo_url
        await uow.flush()
    
    # Генерируем токены
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in),
    )
    await uow.refresh_tokens.add(refresh)
    await uow.commit()
    
    tokens = AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_raw,
        expiresIn=access_ttl,
        refreshExpiresIn=refresh_expires_in,
    )
    return tokens, map_user_model_to_entity(user)


async def register_user_from_bot(
    telegram_id: int,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
    language_code: str | None = None,
    photo_url: str | None = None,
    uow: UoW | None = None
) -> UserEntity:
    """
    Регистрация пользователя из Telegram бота без верификации initData.
    Если пользователь уже существует, обновляет его данные.
    Токены не генерируются.
    """
    if uow is None:
        raise ValueError("UoW is required")
    
    # Проверяем, существует ли пользователь
    user = await uow.users.get_by_telegram_id(telegram_id)
    
    if user is None:
        # Создаем нового пользователя
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
            photo_url=photo_url,
        )
        await uow.users.add(user)
        await uow.flush()
    else:
        # Обновляем данные существующего пользователя
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.language_code = language_code
        user.photo_url = photo_url
        await uow.flush()
    
    await uow.commit()
    return map_user_model_to_entity(user)


async def register_email_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str | None = None,
    uow: UoW | None = None
) -> tuple[AuthTokens, UserEntity]:
    """
    Регистрация нового пользователя по email и паролю.
    
    Args:
        email: Email пользователя (должен быть уникальным)
        password: Пароль в открытом виде
        first_name: Имя пользователя
        last_name: Фамилия пользователя (опционально)
        uow: Unit of Work
        
    Returns:
        Кортеж из токенов авторизации и сущности пользователя
        
    Raises:
        ValueError: Если email уже существует или данные невалидны
    """
    if uow is None:
        raise ValueError("UoW is required")
    
    # Проверка уникальности email
    existing_user = await uow.users.get_by_email(email)
    if existing_user:
        raise ValueError("EMAIL_ALREADY_EXISTS")
    
    # Хеширование пароля
    password_hash = hash_password(password)
    
    # Создание пользователя
    user = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        telegram_id=None,  # Email-пользователь без Telegram
    )
    await uow.users.add(user)
    await uow.flush()
    
    # Генерация токенов (та же логика, что и для Telegram)
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in),
    )
    await uow.refresh_tokens.add(refresh)
    await uow.commit()
    
    tokens = AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_raw,
        expiresIn=access_ttl,
        refreshExpiresIn=refresh_expires_in,
    )
    return tokens, map_user_model_to_entity(user)


async def authenticate_email_user(
    email: str,
    password: str,
    uow: UoW
) -> tuple[AuthTokens, UserEntity]:
    """
    Авторизация пользователя по email и паролю.
    
    Args:
        email: Email пользователя
        password: Пароль в открытом виде
        uow: Unit of Work
        
    Returns:
        Кортеж из токенов авторизации и сущности пользователя
        
    Raises:
        ValueError: Если email или пароль неверны
    """
    user = await uow.users.get_by_email(email)
    if not user or not user.password_hash:
        raise ValueError("INVALID_CREDENTIALS")
    
    if not verify_password(password, user.password_hash):
        raise ValueError("INVALID_CREDENTIALS")
    
    # Генерация токенов (та же логика, что и для Telegram)
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    refresh = RefreshToken(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in),
    )
    await uow.refresh_tokens.add(refresh)
    await uow.commit()
    
    tokens = AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_raw,
        expiresIn=access_ttl,
        refreshExpiresIn=refresh_expires_in,
    )
    return tokens, map_user_model_to_entity(user)


async def refresh_tokens(old_refresh_token: str, uow: UoW) -> AuthTokens:
    token_model = await uow.refresh_tokens.get_by_token(old_refresh_token)
    if not token_model or token_model.revoked or token_model.expires_at <= _utcnow():
        raise PermissionError("INVALID_REFRESH")
    user_id = token_model.user_id
    # Ротация refresh токенов: помечаем старый как отозванный и выдаем новый
    await uow.refresh_tokens.revoke(old_refresh_token, revoked_at=_utcnow())
    new_refresh_raw = generate_refresh_token()
    new_refresh = RefreshToken(
        user_id=user_id,
        token=new_refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS),
    )
    await uow.refresh_tokens.add(new_refresh)
    access_token, access_ttl = create_access_token(user_id)
    await uow.commit()
    return AuthTokens(
        accessToken=access_token,
        refreshToken=new_refresh_raw,
        expiresIn=access_ttl,
        refreshExpiresIn=settings.REFRESH_TOKEN_TTL_SECONDS,
    )
