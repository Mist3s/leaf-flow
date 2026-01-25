from datetime import datetime
from typing import Protocol

from leaf_flow.domain.entities.auth import RefreshTokenEntity


class RefreshTokenWriter(Protocol):
    async def create_refresh_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime
    ) -> RefreshTokenEntity:
        ...

    async def revoke(
        self,
        token: str,
        revoked_at: datetime
    ) -> None:
        ...

    async def revoke_all_for_user(
        self,
        user_id: int,
        revoked_at: datetime
    ) -> None:
        ...


class RefreshTokenReader(Protocol):
    async def get_by_token(self, token: str) -> RefreshTokenEntity | None:
        ...
