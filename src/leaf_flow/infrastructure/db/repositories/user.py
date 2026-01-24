from sqlalchemy import select
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.user import User
from leaf_flow.infrastructure.db.repositories.base import Repository


class UserRepository(Repository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def delete(self, user: User) -> None:
        """Удаляет пользователя из базы данных."""
        await self.session.delete(user)
