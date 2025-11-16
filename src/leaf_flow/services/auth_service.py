from datetime import timedelta, timezone
from uuid import uuid4
from typing import Any

from pydantic import BaseModel

from leaf_flow.config import settings
from leaf_flow.infrastructure.db.models.tokens import RefreshToken
from leaf_flow.infrastructure.db.models.users import User
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services.security import (
    verify_telegram_webapp_request,
    create_access_token,
    generate_refresh_token,
    _utcnow,
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

    # В initData присутствуют serialized telegram fields; парсим минимально
    # Допускаем, что фронт не модифицирует данные Telegram; полная валидация вне скоупа
    from urllib.parse import parse_qsl
    data = dict(parse_qsl(init_data))
    user_json = data.get("user")
    if not user_json:
        raise ValueError("INVALID_INIT_DATA")

    import json
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
    else:
        # Обновляем кэш полей
        user.first_name = tuser.first_name
        user.last_name = tuser.last_name
        user.username = tuser.username
        user.language_code = tuser.language_code
        user.photo_url = tuser.photo_url

    # Генерируем токены
    access_token, access_ttl = create_access_token({"user_id": user.id})
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
    access_token, access_ttl = create_access_token({"user_id": user_id})
    await uow.commit()
    return AuthTokens(
        accessToken=access_token,
        refreshToken=new_refresh_raw,
        expiresIn=access_ttl,
        refreshExpiresIn=settings.REFRESH_TOKEN_TTL_SECONDS,
    )


