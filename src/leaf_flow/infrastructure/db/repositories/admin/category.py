from typing import Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.admin.category import AdminCategoryReader, AdminCategoryWriter
from leaf_flow.domain.entities.category import CategoryEntity
from leaf_flow.infrastructure.db.mappers.category import map_product_category_model_to_entity
from leaf_flow.infrastructure.db.models.product import Category
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminCategoryReaderRepository(Repository[Category], AdminCategoryReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)

    async def get_by_slug(self, slug: str) -> CategoryEntity | None:
        stmt = (
            select(Category)
            .where(Category.slug == slug)
        )
        category = (await self.session.execute(stmt)).scalar_one_or_none()

        if not category:
            return None

        return map_product_category_model_to_entity(category)

    async def list_all(self) -> Sequence[CategoryEntity]:
        stmt = select(Category).order_by(Category.sort_order, Category.slug)
        result = await self.session.execute(stmt)
        categories = result.scalars().all()
        return [map_product_category_model_to_entity(c) for c in categories]


class AdminCategoryWriterRepository(Repository[Category], AdminCategoryWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)

    async def create(
        self,
        slug: str,
        label: str,
        sort_order: int,
    ) -> CategoryEntity:
        category = Category(
            slug=slug,
            label=label,
            sort_order=sort_order,
        )
        self.session.add(category)
        await self.session.flush()
        return map_product_category_model_to_entity(category)

    async def update(self, slug: str, **fields: object) -> CategoryEntity | None:
        allowed = set(Category.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(Category)
            .where(Category.slug == slug)
            .values(**values)
            .returning(Category)
        )
        category = (await self.session.execute(stmt)).scalar_one_or_none()
        await self.session.flush()

        if category is None:
            return None

        return map_product_category_model_to_entity(category)

    async def delete(self, slug: str) -> None:
        stmt = delete(Category).where(Category.slug == slug)
        await self.session.execute(stmt)
        await self.session.flush()
