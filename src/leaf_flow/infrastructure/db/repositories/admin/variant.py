from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.admin.variant import AdminVariantReader, AdminVariantWriter
from leaf_flow.domain.entities.product import ProductVariantEntity
from leaf_flow.infrastructure.db.mappers.product import map_product_variant_model_to_entity
from leaf_flow.infrastructure.db.models.product import ProductVariant
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminVariantReaderRepository(Repository[ProductVariant], AdminVariantReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductVariant)

    async def get_by_id(self, variant_id: str) -> ProductVariantEntity | None:
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
        )
        variant = (await self.session.execute(stmt)).scalar_one_or_none()

        if not variant:
            return None

        return map_product_variant_model_to_entity(variant)

    async def list_by_product(self, product_id: str) -> Sequence[ProductVariantEntity]:
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.sort_order, ProductVariant.id)
        )
        result = await self.session.execute(stmt)
        variants = result.scalars().all()
        return [map_product_variant_model_to_entity(v) for v in variants]


class AdminVariantWriterRepository(Repository[ProductVariant], AdminVariantWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductVariant)

    async def create(
        self,
        id: str,
        product_id: str,
        weight: str,
        price: str,
        is_active: bool,
        sort_order: int,
    ) -> ProductVariantEntity:
        variant = ProductVariant(
            id=id,
            product_id=product_id,
            weight=weight,
            price=Decimal(price),
            is_active=is_active,
            sort_order=sort_order,
        )
        self.session.add(variant)
        await self.session.flush()
        await self.session.refresh(variant)
        return map_product_variant_model_to_entity(variant)

    async def update(
        self, variant_id: str, **fields: object
    ) -> ProductVariantEntity | None:
        allowed = set(ProductVariant.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .values(**values)
            .returning(ProductVariant)
        )
        variant = (await self.session.execute(stmt)).scalar_one_or_none()
        await self.session.flush()

        if variant is None:
            return None

        return map_product_variant_model_to_entity(variant)

    async def delete(self, variant_id: str) -> None:
        stmt = delete(ProductVariant).where(ProductVariant.id == variant_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def set_active(self, variant_id: str, is_active: bool) -> None:
        stmt = (
            update(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .values(is_active=is_active)
        )
        await self.session.execute(stmt)
        await self.session.flush()