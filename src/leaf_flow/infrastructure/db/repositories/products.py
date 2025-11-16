from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.products import Product, ProductVariant, Category
from leaf_flow.infrastructure.db.repositories.base import Repository


class ProductRepository(Repository[Product]):
    def __init__(self, session: Session):
        super().__init__(session, Product)

    async def list_categories(self) -> list[dict[str, str]]:
        rows = (await self.session.execute(select(Category))).scalars().all()
        return [{"id": c.slug, "label": c.label} for c in rows]

    async def search(
        self,
        category_slug: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[Product]]:
        stmt = select(Product)
        if category_slug:
            stmt = stmt.where(Product.category_slug == category_slug)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(Product.name).like(like) | func.lower(func.array_to_string(Product.tags, " ")).like(like)
            )
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total = (await self.session.execute(total_stmt)).scalar_one()
        rows = (await self.session.execute(stmt.order_by(Product.name).limit(limit).offset(offset))).scalars().all()
        return total, rows

    async def get_with_variants(self, product_id: str) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ProductVariantRepository(Repository[ProductVariant]):
    def __init__(self, session: Session):
        super().__init__(session, ProductVariant)

    async def get_for_product(self, product_id: str, variant_id: str) -> ProductVariant | None:
        stmt = select(ProductVariant).where(
            ProductVariant.id == variant_id, ProductVariant.product_id == product_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()


