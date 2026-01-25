from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.auth import RefreshTokenWriter, RefreshTokenReader
from leaf_flow.domain.entities.auth import RefreshTokenEntity
from leaf_flow.infrastructure.db.mappers.auth import map_refresh_token_model_to_entity
from leaf_flow.infrastructure.db.models.token import RefreshToken
from leaf_flow.infrastructure.db.repositories.base import Repository


class RefreshTokenWriterRepository(Repository[RefreshToken], RefreshTokenWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)

    async def create_refresh_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime
    ) -> RefreshTokenEntity:
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return map_refresh_token_model_to_entity(refresh_token)

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


class RefreshTokenReaderRepository(Repository[RefreshToken], RefreshTokenReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)

    async def get_by_token(self, token: str) -> RefreshTokenEntity | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        refresh_token = (await self.session.execute(stmt)).scalar_one_or_none()

        if not refresh_token:
            return None

        return map_refresh_token_model_to_entity(refresh_token)
