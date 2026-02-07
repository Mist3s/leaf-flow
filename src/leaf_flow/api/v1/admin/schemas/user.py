"""Схемы для пользователей в Admin API."""

from pydantic import BaseModel, ConfigDict


class UserDetail(BaseModel):
    id: int
    first_name: str
    last_name: str | None
    username: str | None
    email: str | None
    telegram_id: int | None
    language_code: str | None
    photo_url: str | None

    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    total: int
    items: list[UserDetail]


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
