from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.repositories.image import ImageReaderRepository, ImageWriterRepository
from leaf_flow.application.ports.image import ImageReader, ImageWriter
from leaf_flow.infrastructure.db.session import AsyncSessionLocal



@dataclass
class AdminUoW:
    session: AsyncSession
    images_reader: ImageReader
    images_writer: ImageWriter
    async def flush(self): await self.session.flush()
    async def commit(self): await self.session.commit()
    async def rollback(self): await self.session.rollback()


async def get_admin_uow():
    async with AsyncSessionLocal() as s:
        yield AdminUoW(
            session=s,
            images_reader=ImageReaderRepository(s),
            images_writer=ImageWriterRepository(s)
        )
