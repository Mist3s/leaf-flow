from dataclasses import dataclass
from typing import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.session import AsyncSessionLocal


@dataclass
class AdminUoW:
    """
    Unit of Work для админских операций. Полностью изолирован от публичного UoW.
    """

    session: AsyncSession

    # Только админские репозитории
    # products_reader: AdminProductReader

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


@asynccontextmanager
async def get_admin_uow() -> AsyncIterator[AdminUoW]:
    """Фабрика AdminUoW. Используется как зависимость FastAPI."""
    async with AsyncSessionLocal() as session:
        # Создаём репозитории с общей сессией
        # product_repo = AdminProductRepository(session)

        yield AdminUoW(
            session=session,
            # products_reader=product_repo
        )
