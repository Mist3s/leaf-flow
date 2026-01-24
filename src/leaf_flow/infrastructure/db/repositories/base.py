from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class Repository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get(self, obj_id: int) -> T | None:
        return await self.session.get(self.model, obj_id)

    async def add(self, obj: T) -> T:
        self.session.add(obj)
        return obj
