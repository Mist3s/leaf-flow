from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from leaf_flow.application.ports.admin.attribute import AdminAttributeReader, AdminAttributeValueWriter
from leaf_flow.domain.entities.product import ProductAttributesEntity, ProductAttributesValueEntity
from leaf_flow.infrastructure.db.mappers.admin.attribute import (
    map_attribute_to_entity, map_attribute_value_to_entity
)
from leaf_flow.infrastructure.db.models.product import (
    ProductAttribute,
    ProductAttributeValue,
    ProductAttributeValueLink
)
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminAttributeReaderRepository(Repository[ProductAttribute], AdminAttributeReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductAttribute)

    async def get_by_id(self, attribute_id: int) -> ProductAttributesEntity | None:
        stmt = (
            select(ProductAttribute)
            .where(ProductAttribute.id == attribute_id)
            .options(selectinload(ProductAttribute.values))
        )
        result = await self.session.execute(stmt)
        attr = result.scalar_one_or_none()
        if not attr:
            return None
        return map_attribute_to_entity(attr)

    async def list_all(self) -> Sequence[ProductAttributesEntity]:
        stmt = (
            select(ProductAttribute)
            .options(selectinload(ProductAttribute.values))
            .order_by(ProductAttribute.sort_order, ProductAttribute.id)
        )
        result = await self.session.execute(stmt)
        attrs = result.scalars().all()
        return [map_attribute_to_entity(a) for a in attrs]

    async def get_values_by_attribute(
        self, attribute_id: int
    ) -> Sequence[ProductAttributesValueEntity]:
        stmt = (
            select(ProductAttributeValue)
            .where(ProductAttributeValue.attribute_id == attribute_id)
            .order_by(ProductAttributeValue.sort_order, ProductAttributeValue.id)
        )
        result = await self.session.execute(stmt)
        values = result.scalars().all()
        return [map_attribute_value_to_entity(v) for v in values]


class AdminAttributeValueWriterRepository(
    Repository[ProductAttributeValueLink], AdminAttributeValueWriter
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductAttributeValueLink)

    async def add_to_product(
        self,
        product_id: str,
        attribute_value_id: int,
    ) -> bool:
        # Check if already exists
        stmt = select(ProductAttributeValueLink).where(
            ProductAttributeValueLink.product_id == product_id,
            ProductAttributeValueLink.attribute_value_id == attribute_value_id,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return False  # Already exists

        link = ProductAttributeValueLink(
            product_id=product_id,
            attribute_value_id=attribute_value_id,
        )
        self.session.add(link)
        await self.session.flush()
        return True

    async def remove_from_product(
        self,
        product_id: str,
        attribute_value_id: int,
    ) -> bool:
        stmt = delete(ProductAttributeValueLink).where(
            ProductAttributeValueLink.product_id == product_id,
            ProductAttributeValueLink.attribute_value_id == attribute_value_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[return-value]

    async def set_product_values(
        self,
        product_id: str,
        attribute_value_ids: list[int],
    ) -> bool:
        # Remove all existing links
        await self.session.execute(
            delete(ProductAttributeValueLink).where(
                ProductAttributeValueLink.product_id == product_id
            )
        )

        # Add new links
        for value_id in attribute_value_ids:
            link = ProductAttributeValueLink(
                product_id=product_id,
                attribute_value_id=value_id,
            )
            self.session.add(link)

        await self.session.flush()
        return True
