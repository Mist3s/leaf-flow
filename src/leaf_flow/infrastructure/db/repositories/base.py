from typing import Generic, TypeVar, Type

from sqlalchemy.orm import Session

T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    async def get(self, obj_id: int) -> T | None:
        return await self.session.get(self.model, obj_id)

    async def add(self, obj: T) -> T:
        self.session.add(obj)
        return obj
