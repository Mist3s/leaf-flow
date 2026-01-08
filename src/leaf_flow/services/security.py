import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from operator import itemgetter
from typing import Any, Optional
from urllib.parse import parse_qsl

import bcrypt
import jwt

from leaf_flow.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, expires_in_seconds: Optional[int] = None) -> tuple[str, int]:
    ttl = expires_in_seconds or settings.ACCESS_TOKEN_TTL_SECONDS
    expires_at = _utcnow() + timedelta(seconds=ttl)
    payload = {
        "sub": str(user_id),
        "exp": int(expires_at.timestamp()),
        "iat": int(_utcnow().timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, ttl


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, key=settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def generate_refresh_token() -> str:
    # Оpaque токен, хранится в БД. 32 байта энтропии.
    raw = os.urandom(32)
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def verify_telegram_webapp_request(encoded_init_data: str, bot_token: str) -> bool:
    parsed_data = dict(parse_qsl(encoded_init_data))
    hash_ = parsed_data.pop("hash", None)
    if not hash_:
        return False
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256
    )
    calculated_hash = hmac.new(
        key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return calculated_hash == hash_


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        Хешированный пароль (строка)
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу.
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из БД
        
    Returns:
        True если пароль совпадает, False иначе
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False
