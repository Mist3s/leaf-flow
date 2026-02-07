from typing import Protocol, Sequence

from leaf_flow.domain.entities.user import UserEntity


class AdminUserReader(Protocol):
    async def get_by_id(self, user_id: int) -> UserEntity | None: ...

    async def list_users(
        self,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[UserEntity]]: ...


class AdminUserWriter(Protocol):
    async def update(self, user_id: int, **fields: object) -> UserEntity | None: ...
