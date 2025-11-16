from sqlalchemy import select
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.users import User
from leaf_flow.infrastructure.db.repositories.base import Repository


class UserRepository(Repository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
