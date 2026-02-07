"""Схемы для пользователей в Admin API."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    username: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    language_code: str | None = Field(None, max_length=10)
    photo_url: str | None = Field(None, max_length=500)
