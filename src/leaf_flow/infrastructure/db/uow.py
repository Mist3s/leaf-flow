from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.repositories.users import UserRepository
from leaf_flow.infrastructure.db.session import AsyncSessionLocal


@dataclass
class UoW:
    session: AsyncSession
    users: UserRepository
    async def commit(self): await self.session.commit()
    async def rollback(self): await self.session.rollback()


async def get_uow():
    async with AsyncSessionLocal() as s:
        yield UoW(session=s, users=UserRepository(s))
