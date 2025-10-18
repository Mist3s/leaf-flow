from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from leaf_flow.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def get_async_session():
    async with AsyncSessionLocal() as s:
        yield s
