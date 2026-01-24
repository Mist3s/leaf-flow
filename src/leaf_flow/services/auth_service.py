import json
from datetime import timedelta
from urllib.parse import parse_qsl

from pydantic import BaseModel

from leaf_flow.config import settings
from leaf_flow.infrastructure.db.models.token import RefreshToken
from leaf_flow.infrastructure.db.models.user import User
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
from leaf_flow.infrastructure.db.mappers.user import map_user_model_to_entity


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
    if not verify_telegram_webapp_request(
        init_data,
        settings.TELEGRAM_BOT_TOKEN
    ):
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
    if not verify_telegram_login_widget(
        widget_data,
        settings.TELEGRAM_BOT_TOKEN
    ):
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


async def link_telegram_to_user(
    widget_data: dict,
    current_user_id: int,
    uow: UoW
) -> UserEntity:
    """
    Привязывает Telegram-аккаунт к существующему пользователю.
    
    Если telegram_id уже привязан к другому аккаунту, возвращает ошибку.
    Для слияния аккаунтов используйте merge_telegram_account.
    
    Args:
        widget_data: Данные от Login Widget (id, first_name, auth_date, hash, ...)
        current_user_id: ID текущего авторизованного пользователя
        uow: Unit of Work
        
    Returns:
        Обновлённая сущность пользователя
        
    Raises:
        ValueError: Если данные невалидны, Telegram уже привязан или занят другим аккаунтом
    """
    # Валидация подписи и auth_date
    if not verify_telegram_login_widget(
        widget_data,
        settings.TELEGRAM_BOT_TOKEN
    ):
        raise ValueError("INVALID_LOGIN_WIDGET_DATA")
    
    telegram_id = widget_data["id"]
    first_name = widget_data["first_name"]
    last_name = widget_data.get("last_name")
    username = widget_data.get("username")
    photo_url = widget_data.get("photo_url")
    
    # Получаем текущего пользователя
    current_user = await uow.users.get(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, не привязан ли уже Telegram к этому пользователю
    if current_user.telegram_id is not None:
        raise ValueError("TELEGRAM_ALREADY_LINKED")
    
    # Проверяем, не занят ли этот telegram_id другим аккаунтом
    existing_tg_user = await uow.users.get_by_telegram_id(telegram_id)
    
    if existing_tg_user:
        if existing_tg_user.id == current_user_id:
            raise ValueError("TELEGRAM_ALREADY_LINKED")
        # Telegram привязан к другому аккаунту — нужно слияние
        raise ValueError("TELEGRAM_LINKED_TO_ANOTHER_ACCOUNT")
    
    # Привязываем Telegram к текущему пользователю
    current_user.telegram_id = telegram_id
    current_user.username = username
    current_user.photo_url = photo_url
    # Обновляем имя только если у пользователя оно не задано или пустое
    if not current_user.first_name:
        current_user.first_name = first_name
    if not current_user.last_name and last_name:
        current_user.last_name = last_name
    
    await uow.commit()
    return map_user_model_to_entity(current_user)


async def merge_telegram_account(
    widget_data: dict,
    current_user_id: int,
    uow: UoW
) -> UserEntity:
    """
    Выполняет слияние аккаунтов: привязывает Telegram к текущему пользователю,
    перенося данные со старого Telegram-аккаунта.
    
    Слияние:
    - Заказы переносятся на текущего пользователя
    - Корзина старого аккаунта удаляется
    - Старый аккаунт удаляется
    
    Args:
        widget_data: Данные от Login Widget (id, first_name, auth_date, hash, ...)
        current_user_id: ID текущего авторизованного пользователя
        uow: Unit of Work
        
    Returns:
        Обновлённая сущность пользователя
        
    Raises:
        ValueError: Если данные невалидны или слияние невозможно
    """
    # Валидация подписи и auth_date
    if not verify_telegram_login_widget(widget_data, settings.TELEGRAM_BOT_TOKEN):
        raise ValueError("INVALID_LOGIN_WIDGET_DATA")
    
    telegram_id = widget_data["id"]
    first_name = widget_data["first_name"]
    last_name = widget_data.get("last_name")
    username = widget_data.get("username")
    photo_url = widget_data.get("photo_url")
    
    # Получаем текущего пользователя
    current_user = await uow.users.get(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, не привязан ли уже Telegram к этому пользователю
    if current_user.telegram_id is not None:
        raise ValueError("TELEGRAM_ALREADY_LINKED")
    
    # Проверяем, существует ли аккаунт с этим telegram_id
    existing_tg_user = await uow.users.get_by_telegram_id(telegram_id)
    
    if not existing_tg_user:
        # Нет аккаунта для слияния — просто привязываем
        current_user.telegram_id = telegram_id
        current_user.username = username
        current_user.photo_url = photo_url
        if not current_user.first_name:
            current_user.first_name = first_name
        if not current_user.last_name and last_name:
            current_user.last_name = last_name
        await uow.commit()
        return map_user_model_to_entity(current_user)
    
    if existing_tg_user.id == current_user_id:
        raise ValueError("TELEGRAM_ALREADY_LINKED")
    
    # === СЛИЯНИЕ АККАУНТОВ ===
    # 1. Переносим заказы на текущего пользователя
    await uow.orders_writer.transfer_orders_to_user(
        from_user_id=existing_tg_user.id,
        to_user_id=current_user_id
    )
    
    # 2. Очищаем корзину старого пользователя (удаляем её)
    await uow.carts_writer.delete_by_user_id(existing_tg_user.id)
    
    # 3. Отзываем все refresh токены старого пользователя
    await uow.refresh_tokens.revoke_all_for_user(existing_tg_user.id, _utcnow())
    
    # 4. Удаляем старого пользователя и сразу применяем изменения,
    #    чтобы освободить telegram_id до UPDATE
    await uow.users.delete(existing_tg_user)
    await uow.flush()
    
    # 5. Привязываем Telegram к текущему пользователю
    current_user.telegram_id = telegram_id
    current_user.username = username
    current_user.photo_url = photo_url
    if not current_user.first_name:
        current_user.first_name = first_name
    if not current_user.last_name and last_name:
        current_user.last_name = last_name
    
    await uow.commit()
    return map_user_model_to_entity(current_user)


async def unlink_telegram_from_user(
    current_user_id: int,
    uow: UoW
) -> UserEntity:
    """
    Отвязывает Telegram от аккаунта пользователя.
    
    Отвязка возможна только если у пользователя есть email и пароль,
    чтобы он мог продолжить входить в аккаунт.
    
    Args:
        current_user_id: ID текущего авторизованного пользователя
        uow: Unit of Work
        
    Returns:
        Обновлённая сущность пользователя
        
    Raises:
        ValueError: Если у пользователя нет Telegram или нет email/пароля
    """
    current_user = await uow.users.get(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, привязан ли Telegram
    if current_user.telegram_id is None:
        raise ValueError("TELEGRAM_NOT_LINKED")
    
    # Проверяем, есть ли альтернативный способ входа (email + пароль)
    if not current_user.email or not current_user.password_hash:
        raise ValueError("CANNOT_UNLINK_NO_EMAIL_PASSWORD")
    
    # Отвязываем Telegram
    current_user.telegram_id = None
    current_user.username = None  # username связан с Telegram
    current_user.photo_url = None  # фото тоже из Telegram
    
    await uow.commit()
    return map_user_model_to_entity(current_user)


async def update_user_profile(
    current_user_id: int,
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    uow: UoW
) -> UserEntity:
    """
    Обновляет профиль пользователя (имя, фамилия, email).
    
    Args:
        current_user_id: ID текущего пользователя
        first_name: Новое имя (None = не менять)
        last_name: Новая фамилия (None = не менять)
        email: Новый email (None = не менять)
        uow: Unit of Work
        
    Returns:
        Обновлённая сущность пользователя
        
    Raises:
        ValueError: Если пользователь не найден или email уже занят
    """
    current_user = await uow.users.get(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Обновляем имя
    if first_name is not None:
        current_user.first_name = first_name
    
    # Обновляем фамилию
    if last_name is not None:
        current_user.last_name = last_name
    
    # Обновляем email
    if email is not None and email != current_user.email:
        # Проверяем, не занят ли email другим пользователем
        existing_user = await uow.users.get_by_email(email)
        if existing_user and existing_user.id != current_user_id:
            raise ValueError("EMAIL_ALREADY_EXISTS")
        current_user.email = email
    
    await uow.commit()
    return map_user_model_to_entity(current_user)


async def change_user_password(
    current_user_id: int,
    current_password: str | None,
    new_password: str,
    uow: UoW
) -> UserEntity:
    """
    Изменяет или создаёт пароль пользователя.
    
    - Если пароль уже установлен, требуется current_password для проверки
    - Если пароля нет (Telegram-пользователь), current_password не нужен
    
    Args:
        current_user_id: ID текущего пользователя
        current_password: Текущий пароль (обязателен, если пароль уже установлен)
        new_password: Новый пароль
        uow: Unit of Work
        
    Returns:
        Обновлённая сущность пользователя
        
    Raises:
        ValueError: Если текущий пароль неверен или пользователь не найден
    """
    current_user = await uow.users.get(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Если пароль уже установлен, проверяем текущий пароль
    if current_user.password_hash:
        if not current_password:
            raise ValueError("CURRENT_PASSWORD_REQUIRED")
        if not verify_password(current_password, current_user.password_hash):
            raise ValueError("INVALID_CURRENT_PASSWORD")
    
    # Устанавливаем новый пароль
    current_user.password_hash = hash_password(new_password)
    
    await uow.commit()
    return map_user_model_to_entity(current_user)


async def set_user_email(
    current_user_id: int,
    email: str,
    password: str,
    uow: UoW
) -> UserEntity:
    """
    Устанавливает email и пароль для пользователя без email (Telegram-пользователь).
    
    Args:
        current_user_id: ID текущего пользователя
        email: Email для привязки
        password: Пароль для нового способа входа
        uow: Unit of Work
        
    Returns:
        Обновлённая сущность пользователя
        
    Raises:
        ValueError: Если email уже есть, занят другим пользователем, или пользователь не найден
    """
    current_user = await uow.users.get(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, что email ещё не установлен
    if current_user.email:
        raise ValueError("EMAIL_ALREADY_SET")
    
    # Проверяем, не занят ли email другим пользователем
    existing_user = await uow.users.get_by_email(email)
    if existing_user:
        raise ValueError("EMAIL_ALREADY_EXISTS")
    
    # Устанавливаем email и пароль
    current_user.email = email
    current_user.password_hash = hash_password(password)
    
    await uow.commit()
    return map_user_model_to_entity(current_user)
