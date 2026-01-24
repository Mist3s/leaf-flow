from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.category import CategoryReader
from leaf_flow.infrastructure.db.mappers.category import map_product_category_model_to_entity
from leaf_flow.infrastructure.db.models.products import Category
from leaf_flow.infrastructure.db.repositories.base import Repository
from leaf_flow.domain.entities.category import CategoryEntity


class CategoryReaderRepository(Repository[Category], CategoryReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)

    async def get_by_slug(self, slug: str) -> CategoryEntity | None:
        category = await self.session.execute(select(Category).where(Category.slug == slug))
        return map_product_category_model_to_entity(category.scalar_one_or_none())

    async def list_categories(self) -> Sequence[CategoryEntity]:
        rows = (await self.session.execute(select(Category))).scalars().all()
        return [map_product_category_model_to_entity(category) for category in rows]
