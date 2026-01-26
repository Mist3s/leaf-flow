from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from leaf_flow.infrastructure.db.mappers.user import map_user_model_to_entity
from leaf_flow.infrastructure.db.models.user import User
from leaf_flow.infrastructure.db.repositories.base import Repository
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.application.ports.user import UserReader, UserWriter


class UserReaderRepository(Repository[User], UserReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_id(
        self,
        user_id: int
    ) -> UserEntity | None:
        stmt = select(User).where(User.id == user_id)
        user = (await self.session.execute(stmt)).scalar_one_or_none()

        if user is None:
            return None

        return map_user_model_to_entity(user)

    async def get_by_telegram_id(
        self,
        telegram_id: int
    ) -> UserEntity | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = (await self.session.execute(stmt)).scalar_one_or_none()

        if user is None:
            return None

        return map_user_model_to_entity(user)

    async def get_by_email(
        self,
        email: str
    ) -> UserEntity | None:
        stmt = select(User).where(User.email == email)
        user = (await self.session.execute(stmt)).scalar_one_or_none()

        if user is None:
            return None

        return map_user_model_to_entity(user)


class UserWriterRepository(Repository[User], UserWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

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
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
            photo_url=photo_url,
            email=email,
            password_hash=password_hash
        )
        self.session.add(user)
        await self.session.flush()
        return map_user_model_to_entity(user)

    async def delete(
        self,
        user_id: int
    ) -> None:
        stmt = delete(User).where(User.id == user_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def update_fields(self, user_id: int, **fields) -> UserEntity | None:
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
