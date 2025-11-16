from sqlalchemy import select
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.products import Category
from leaf_flow.infrastructure.db.repositories.base import Repository


class CategoryRepository(Repository[Category]):
    def __init__(self, session: Session):
        super().__init__(session, Category)

    async def get_by_slug(self, slug: str) -> Category | None:
        return (await self.session.execute(select(Category).where(Category.slug == slug))).scalar_one_or_none()


