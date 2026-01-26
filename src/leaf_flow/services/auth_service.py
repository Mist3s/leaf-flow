from datetime import timedelta

from leaf_flow.application.auth.exceptions import InvalidInitData, InvalidWidgetData
from leaf_flow.application.dto.auth import AuthTokens
from leaf_flow.config import settings
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.infrastructure.externals.telegram.parser import (
    parse_telegram_init_data, parse_telegram_widget_data
)
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


async def exchange_init_data_for_tokens(init_data: str, uow: UoW) -> tuple[AuthTokens, UserEntity]:
    if not verify_telegram_webapp_request(
        init_data,
        settings.TELEGRAM_BOT_TOKEN
    ):
        raise InvalidInitData("INVALID_INIT_DATA")

    telegram_user = parse_telegram_init_data(init_data)
    user = await uow.users_reader.get_by_telegram_id(telegram_user.telegram_id)

    if user is None:
        user = await uow.users_writer.create(
            telegram_id=telegram_user.telegram_id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
            language_code=telegram_user.language_code,
            photo_url=telegram_user.photo_url
        )
    else:
        # Обновляем данные существующего пользователя
        user = await uow.users_writer.update_fields(
            user_id=user.id,
            username=telegram_user.username,
            photo_url=telegram_user.photo_url,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name
        )

    # Генерируем токены
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    await uow.refresh_tokens_writer.create_refresh_token(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in)
    )
    await uow.commit()

    tokens = AuthTokens(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=access_ttl,
        refresh_expires_in=refresh_expires_in,
    )
    return tokens, user


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
        raise InvalidWidgetData("INVALID_LOGIN_WIDGET_DATA")

    telegram_user = parse_telegram_widget_data(widget_data)
    user = await uow.users_reader.get_by_telegram_id(telegram_user.telegram_id)
    
    if user is None:
        user = await uow.users_writer.create(
            telegram_id=telegram_user.telegram_id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
            photo_url=telegram_user.photo_url
        )
    else:
        # Обновляем данные существующего пользователя
        user = await uow.users_writer.update_fields(
            user_id=user.id,
            username=telegram_user.username,
            photo_url=telegram_user.photo_url,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name
        )
    
    # Генерируем токены
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    await uow.refresh_tokens_writer.create_refresh_token(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in)
    )
    await uow.commit()

    tokens = AuthTokens(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=access_ttl,
        refresh_expires_in=refresh_expires_in,
    )
    return tokens, user


async def register_user_from_bot(
    telegram_id: int,
    first_name: str,
    uow: UoW,
    last_name: str | None = None,
    username: str | None = None,
    language_code: str | None = None,
    photo_url: str | None = None
) -> UserEntity:
    """
    Регистрация пользователя из Telegram бота без верификации initData.
    Если пользователь уже существует, обновляет его данные.
    Токены не генерируются.
    """
    # Проверяем, существует ли пользователь
    user = await uow.users_reader.get_by_telegram_id(telegram_id)
    
    if user is None:
        # Создаем нового пользователя
        user = await uow.users_writer.create(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
            photo_url=photo_url
        )
    else:
        # Обновляем данные существующего пользователя
        user = await uow.users_writer.update_fields(
            user_id=user.id,
            username=username,
            photo_url=photo_url,
            first_name=first_name,
            last_name=last_name
        )
    
    await uow.commit()
    return user


async def register_email_user(
    email: str,
    password: str,
    first_name: str,
    uow: UoW,
    last_name: str | None = None
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
    
    # Проверка уникальности email
    existing_user = await uow.users_reader.get_by_email(email)

    if existing_user:
        raise ValueError("EMAIL_ALREADY_EXISTS")
    
    # Хеширование пароля
    password_hash = hash_password(password)
    
    # Создание пользователя
    user = await uow.users_writer.create(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
    )
    await uow.flush()
    
    # Генерация токенов (та же логика, что и для Telegram)
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    await uow.refresh_tokens_writer.create_refresh_token(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in)
    )
    await uow.commit()

    tokens = AuthTokens(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=access_ttl,
        refresh_expires_in=refresh_expires_in,
    )
    return tokens, user


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
    user = await uow.users_reader.get_by_email(email)

    if not user or not user.password_hash:
        raise ValueError("INVALID_CREDENTIALS")
    
    if not verify_password(password, user.password_hash):
        raise ValueError("INVALID_CREDENTIALS")
    
    # Генерация токенов (та же логика, что и для Telegram)
    access_token, access_ttl = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    refresh_expires_in = settings.REFRESH_TOKEN_TTL_SECONDS
    await uow.refresh_tokens_writer.create_refresh_token(
        user_id=user.id,
        token=refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=refresh_expires_in)
    )
    await uow.commit()

    tokens = AuthTokens(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=access_ttl,
        refresh_expires_in=refresh_expires_in,
    )
    return tokens, user


async def refresh_tokens(old_refresh_token: str, uow: UoW) -> AuthTokens:
    refresh_token = await uow.refresh_tokens_reader.get_by_token(old_refresh_token)

    if not refresh_token or refresh_token.revoked or refresh_token.expires_at <= _utcnow():
        raise PermissionError("INVALID_REFRESH")

    # Ротация refresh токенов: помечаем старый как отозванный и выдаем новый
    await uow.refresh_tokens_writer.revoke(
        old_refresh_token,
        revoked_at=_utcnow()
    )

    new_refresh_raw = generate_refresh_token()

    await uow.refresh_tokens_writer.create_refresh_token(
        user_id=refresh_token.user_id,
        token=new_refresh_raw,
        expires_at=_utcnow() + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS)
    )
    await uow.commit()
    access_token, access_ttl = create_access_token(refresh_token.user_id)

    return AuthTokens(
        access_token=access_token,
        refresh_token=new_refresh_raw,
        expires_in=access_ttl,
        refresh_expires_in=settings.REFRESH_TOKEN_TTL_SECONDS,
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
    if not verify_telegram_login_widget(
            widget_data,
            settings.TELEGRAM_BOT_TOKEN
    ):
        raise InvalidWidgetData("INVALID_LOGIN_WIDGET_DATA")

    telegram_user = parse_telegram_widget_data(widget_data)
    
    # Получаем текущего пользователя
    current_user = await uow.users_reader.get_by_id(current_user_id)

    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, не привязан ли уже Telegram к этому пользователю
    if current_user.telegram_id is not None:
        raise ValueError("TELEGRAM_ALREADY_LINKED")
    
    # Проверяем, не занят ли этот telegram_id другим аккаунтом
    existing_tg_user = await uow.users_reader.get_by_telegram_id(
        telegram_user.telegram_id
    )
    
    if existing_tg_user:
        if existing_tg_user.id == current_user_id:
            raise ValueError("TELEGRAM_ALREADY_LINKED")
        # Telegram привязан к другому аккаунту — нужно слияние
        raise ValueError("TELEGRAM_LINKED_TO_ANOTHER_ACCOUNT")
    
    # Привязываем Telegram к текущему пользователю

    user_up = await uow.users_writer.update_fields(
        user_id=current_user_id,
        telegram_id=telegram_user.telegram_id,
        username=telegram_user.username,
        photo_url=telegram_user.photo_url
    )
    await uow.commit()
    return user_up


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

    telegram_user = parse_telegram_widget_data(widget_data)
    
    # Получаем текущего пользователя
    current_user = await uow.users_reader.get_by_id(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, не привязан ли уже Telegram к этому пользователю
    if current_user.telegram_id is not None:
        raise ValueError("TELEGRAM_ALREADY_LINKED")
    
    # Проверяем, существует ли аккаунт с этим telegram_id
    existing_tg_user = await uow.users_reader.get_by_telegram_id(
        telegram_user.telegram_id
    )
    
    if not existing_tg_user:
        # Нет аккаунта для слияния — просто привязываем
        await uow.users_writer.update_fields(
            user_id=current_user_id,
            telegram_id=telegram_user.telegram_id,
            username=telegram_user.username,
            photo_url=telegram_user.photo_url
        )
        await uow.commit()
        return current_user
    
    if existing_tg_user.id == current_user_id:
        raise ValueError("TELEGRAM_ALREADY_LINKED")
    
    # === СЛИЯНИЕ АККАУНТОВ ===
    # 1. Переносим заказы на текущего пользователя
    await uow.orders_writer.transfer_orders_to_user(
        from_user_id=existing_tg_user.id,
        to_user_id=current_user_id
    )
    
    # 2. Удаляем старого пользователя и сразу применяем изменения,
    #    чтобы освободить telegram_id до UPDATE
    await uow.users_writer.delete(existing_tg_user.id)

    user_up = await uow.users_writer.update_fields(
        user_id=current_user_id,
        telegram_id=telegram_user.telegram_id,
        username=telegram_user.username,
        photo_url=telegram_user.photo_url
    )
    await uow.commit()
    return user_up


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
    current_user = await uow.users_reader.get_by_id(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, привязан ли Telegram
    if current_user.telegram_id is None:
        raise ValueError("TELEGRAM_NOT_LINKED")
    
    # Проверяем, есть ли альтернативный способ входа (email + пароль)
    if not current_user.email or not current_user.password_hash:
        raise ValueError("CANNOT_UNLINK_NO_EMAIL_PASSWORD")

    user_up = await uow.users_writer.update_fields(
        user_id=current_user_id,
        telegram_id=None,
        username=None,
        photo_url=None
    )
    await uow.commit()
    return user_up


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
    current_user = await uow.users_reader.get_by_id(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")

    update_fields = {}

    # Обновляем имя
    if first_name is not None:
        update_fields['first_name'] = first_name
    
    # Обновляем фамилию
    if last_name is not None:
        update_fields['last_name'] = last_name
    
    # Обновляем email
    if email is not None and email != current_user.email:
        # Проверяем, не занят ли email другим пользователем
        existing_user = await uow.users_reader.get_by_email(email)

        if existing_user and existing_user.id != current_user_id:
            raise ValueError("EMAIL_ALREADY_EXISTS")

        update_fields['email'] = email

    user_up = await uow.users_writer.update_fields(
        user_id=current_user_id,
        **update_fields
    )
    await uow.commit()
    return user_up


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
    current_user = await uow.users_reader.get_by_id(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Если пароль уже установлен, проверяем текущий пароль
    if current_user.password_hash:
        if not current_password:
            raise ValueError("CURRENT_PASSWORD_REQUIRED")
        if not verify_password(current_password, current_user.password_hash):
            raise ValueError("INVALID_CURRENT_PASSWORD")
    
    # Устанавливаем новый пароль
    user_up = await uow.users_writer.update_fields(
        user_id=current_user_id,
        password_hash=hash_password(new_password)
    )
    await uow.commit()
    return user_up


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
    current_user = await uow.users_reader.get_by_id(current_user_id)
    if not current_user:
        raise ValueError("USER_NOT_FOUND")
    
    # Проверяем, что email ещё не установлен
    if current_user.email:
        raise ValueError("EMAIL_ALREADY_SET")
    
    # Проверяем, не занят ли email другим пользователем
    existing_user = await uow.users_reader.get_by_email(email)
    if existing_user:
        raise ValueError("EMAIL_ALREADY_EXISTS")
    
    # Устанавливаем email и пароль
    user_up = await uow.users_writer.update_fields(
        user_id=current_user_id,
        email=email,
        password_hash=hash_password(password)
    )
    await uow.commit()
    return user_up
