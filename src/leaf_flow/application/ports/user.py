from typing import Protocol

from leaf_flow.domain.entities.user import UserEntity


class UserReader(Protocol):
    async def get_by_id(
        self,
        user_id: int
    ) -> UserEntity | None:
        ...

    async def get_by_telegram_id(
        self,
        telegram_id: int
    ) -> UserEntity | None:
        ...

    async def get_by_email(
        self,
        email: str
    ) -> UserEntity | None:
        ...


class UserWriter(Protocol):
    async def create(
        self,
        first_name: str,
        telegram_id: int | None = None,
        last_name: str | None = None,
        username: str | None = None,
        language_code: str | None = None,
        photo_url: str | None = None,
        email: str | None = None,
        password_hash: str | None = None
    ) -> UserEntity:
        ...

    async def delete(
        self,
        user_id: int
    ) -> None:
        ...

    async def update_fields(
        self,
        user_id: int,
        **fields
    ) -> UserEntity | None:
        ...
