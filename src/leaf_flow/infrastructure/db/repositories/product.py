from typing import Sequence

from sqlalchemy import select, func, or_, tuple_
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.product import ProductsReader
from leaf_flow.domain.entities.product import ProductEntity, ProductDetailEntity, ProductVariantEntity

from leaf_flow.infrastructure.db.models.product import (
    Product, ProductVariant, ProductAttributeValue,
    ProductBrewProfile, ProductImage, ProductAttribute
)
from leaf_flow.infrastructure.db.repositories.base import Repository
from leaf_flow.infrastructure.db.mappers.product import (
    map_product_model_to_entity,
    map_product_detail_model_to_entity,
    map_product_variant_model_to_entity
)

class ProductRepository(Repository[Product], ProductsReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def get_list_products(
        self,
        category_slug: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[ProductEntity]]:

        stmt = (
            select(Product)
            .where(Product.is_active.is_(True))
            .options(
                selectinload(Product.variants),
                with_loader_criteria(
                    ProductVariant,
                    ProductVariant.is_active.is_(True),
                    include_aliases=True
                )
            )
        )

        if category_slug:
            stmt = stmt.where(Product.category_slug == category_slug)

        if search:
            s = search.lower()
            like_pattern = f"%{s}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(like_pattern),
                    Product.description.ilike(like_pattern),
                    Product.tags.contains([s]),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        rows = (
            await self.session.execute(
                stmt.order_by(Product.name).limit(limit).offset(offset)
            )
        ).scalars().all()

        return total, [map_product_model_to_entity(p) for p in rows]

    async def get_with_variants(self, product_id: str) -> ProductDetailEntity | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.is_active.is_(True))
            .options(
                selectinload(Product.variants),
                selectinload(
                    Product.attribute_values
                ).selectinload(
                    ProductAttributeValue.attribute
                ),
                selectinload(Product.brew_profiles),
                selectinload(Product.images).selectinload(ProductImage.variants),

                with_loader_criteria(
                    ProductVariant,
                    ProductVariant.is_active.is_(True),
                    include_aliases=True
                ),
                with_loader_criteria(
                    ProductBrewProfile,
                    ProductBrewProfile.is_active.is_(True),
                    include_aliases=True
                ),
                with_loader_criteria(
                    ProductImage,
                    ProductImage.is_active.is_(True),
                    include_aliases=True
                ),
                with_loader_criteria(
                    ProductAttributeValue,
                    ProductAttributeValue.is_active.is_(True),
                    include_aliases=True
                ),
                with_loader_criteria(
                    ProductAttribute,
                    ProductAttribute.is_active.is_(True),
                    include_aliases=True
                ),
            )
        )
        result = await self.session.execute(stmt)
        return map_product_detail_model_to_entity(result.scalar_one_or_none())

    async def get_for_product_variant(
        self,
        product_id: str,
        variant_id: str
    ) -> ProductVariantEntity | None:
        stmt = select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id
        )
        variant = await self.session.execute(stmt)
        return map_product_variant_model_to_entity(variant.scalar_one_or_none())

    async def get_for_product_variants(
        self,
        keys: list[tuple[str, str]]
    ) -> dict[tuple[str, str], ProductVariantEntity]:
        stmt = (
            select(ProductVariant)
            .where(
                tuple_(
                    ProductVariant.product_id,
                    ProductVariant.id
                ).in_(keys)
            )
        )

        result = await self.session.execute(stmt)
        variants = result.scalars().all()

        return {
            (
                v.product_id,
                v.id
            ): map_product_variant_model_to_entity(v) for v in variants
        }
