from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.tokens import RefreshToken
from leaf_flow.infrastructure.db.repositories.base import Repository


class RefreshTokenRepository(Repository[RefreshToken]):
    def __init__(self, session: Session):
        super().__init__(session, RefreshToken)

    async def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def revoke(self, token: str, revoked_at: datetime) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(revoked=True, revoked_at=revoked_at)
        )

    async def revoke_all_for_user(self, user_id: int, revoked_at: datetime) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True, revoked_at=revoked_at)
        )
