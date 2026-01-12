from typing import Sequence

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload

from leaf_flow.infrastructure.db.models.products import Product, ProductVariant, Category, ProductAttributeValue
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
        stmt = (
            select(Product)
            .options(
                selectinload(Product.variants),
                selectinload(Product.attribute_values).selectinload(ProductAttributeValue.attribute),
            )
        )

        if category_slug:
            stmt = stmt.where(Product.category_slug == category_slug)

        if search:
            search_lower = search.lower()
            like_pattern = f"%{search_lower}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(like_pattern),
                    Product.tags.contains([search_lower]),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        rows = (
            await self.session.execute(
                stmt.order_by(Product.name).limit(limit).offset(offset)
            )
        ).scalars().all()

        return total, rows

    async def get_with_variants(self, product_id: str) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.attribute_values).selectinload(ProductAttributeValue.attribute),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multiple_with_variants(self, product_ids: list[str]) -> dict[str, Product]:
        """
        Загружает несколько продуктов с их вариантами одним запросом.
        Возвращает словарь product_id -> Product.
        """
        if not product_ids:
            return {}
        stmt = select(Product).options(selectinload(Product.variants)).where(Product.id.in_(product_ids))
        result = await self.session.execute(stmt)
        products = result.scalars().all()
        return {p.id: p for p in products}


class ProductVariantRepository(Repository[ProductVariant]):
    def __init__(self, session: Session):
        super().__init__(session, ProductVariant)

    async def get_for_product(self, product_id: str, variant_id: str) -> ProductVariant | None:
        stmt = select(ProductVariant).where(
            ProductVariant.id == variant_id, ProductVariant.product_id == product_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_multiple(self, keys: list[tuple[str, str]]) -> dict[tuple[str, str], ProductVariant]:
        """
        Батчевая загрузка вариантов по списку (product_id, variant_id).
        Возвращает словарь (product_id, variant_id) -> ProductVariant.
        """
        if not keys:
            return {}
        # Формируем список variant_id для IN-запроса
        variant_ids = [variant_id for _, variant_id in keys]
        stmt = select(ProductVariant).where(ProductVariant.id.in_(variant_ids))
        result = await self.session.execute(stmt)
        variants = result.scalars().all()
        # Фильтруем только те, которые соответствуют запрошенным парам
        key_set = set(keys)
        return {
            (v.product_id, v.id): v for v in variants
            if (v.product_id, v.id) in key_set
        }

    async def delete(self, variant: ProductVariant) -> None:
        await self.session.delete(variant)

