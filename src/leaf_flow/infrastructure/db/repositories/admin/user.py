from typing import Sequence

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.admin.user import AdminUserReader, AdminUserWriter
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.mappers.user import map_user_model_to_entity
from leaf_flow.infrastructure.db.models.user import User
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminUserReaderRepository(Repository[User], AdminUserReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_id(self, user_id: int) -> UserEntity | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()

        if not user:
            return None

        return map_user_model_to_entity(user)

    async def list_users(
        self,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[UserEntity]]:
        stmt = select(User)
        count_stmt = select(func.count(User.id))

        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(User.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        users = result.scalars().all()

        return total, [map_user_model_to_entity(u) for u in users]


class AdminUserWriterRepository(Repository[User], AdminUserWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def update(self, user_id: int, **fields: object) -> UserEntity | None:
        allowed = set(User.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**values)
            .returning(User)
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        await self.session.flush()

        if user is None:
            return None

        return map_user_model_to_entity(user)
