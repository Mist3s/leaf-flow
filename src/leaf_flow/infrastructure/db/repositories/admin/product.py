from typing import Sequence

from sqlalchemy import func, select, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from leaf_flow.application.ports.admin.product import AdminProductReader, AdminProductWriter
from leaf_flow.domain.entities.product import ProductDetailEntity
from leaf_flow.infrastructure.db.mappers.product import map_product_detail_model_to_entity
from leaf_flow.infrastructure.db.models.product import (
    Product,
    ProductAttributeValue,
    ProductImage
)
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminProductReaderRepository(Repository[Product], AdminProductReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def get_by_id(self, product_id: str) -> ProductDetailEntity | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.brew_profiles),
                selectinload(Product.images).selectinload(ProductImage.variants),
                selectinload(Product.attribute_values).selectinload(
                    ProductAttributeValue.attribute
                ),
            )
        )
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            return None
        return map_product_detail_model_to_entity(product)

    async def list_products(
        self,
        search: str | None,
        category_slug: str | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[ProductDetailEntity]]:
        stmt = select(Product).options(
            selectinload(Product.variants),
            selectinload(Product.brew_profiles),
            selectinload(Product.images).selectinload(ProductImage.variants),
            selectinload(Product.attribute_values).selectinload(
                ProductAttributeValue.attribute
            ),
        )
        count_stmt = select(func.count(Product.id))

        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.id.ilike(f"%{search}%"),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if category_slug:
            stmt = stmt.where(Product.category_slug == category_slug)
            count_stmt = count_stmt.where(Product.category_slug == category_slug)

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
            count_stmt = count_stmt.where(Product.is_active == is_active)

        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        products = result.scalars().all()

        return total, [map_product_detail_model_to_entity(p) for p in products]


class AdminProductWriterRepository(Repository[Product], AdminProductWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def create(
        self,
        id: str,
        name: str,
        description: str,
        category_slug: str,
        image: str,
        product_type_code: str,
        tags: list[str],
        is_active: bool,
    ) -> ProductDetailEntity:
        product = Product(
            id=id,
            name=name,
            description=description,
            category_slug=category_slug,
            image=image,
            product_type_code=product_type_code,
            tags=tags,
            is_active=is_active,
        )
        self.session.add(product)
        await self.session.flush()

        return ProductDetailEntity(
            id=product.id,
            name=product.name,
            description=product.description,
            category_slug=product.category_slug,
            image=product.image,
            product_type_code=product.product_type_code,
            tags=list(product.tags or []),
            variants=[],
            brew_profiles=[],
            attribute_values=[],
            images=[],
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            sort_order=product.sort_order,
        )

    async def update(
        self,
        product_id: str,
        **fields: object,
    ) -> ProductDetailEntity | None:
        allowed = set(Product.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(**values)
            .returning(Product)
        )
        await self.session.execute(stmt)
        await self.session.flush()

        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.brew_profiles),
                selectinload(Product.images).selectinload(ProductImage.variants),
                selectinload(Product.attribute_values).selectinload(
                    ProductAttributeValue.attribute
                ),
            )
        )
        result = await self.session.execute(stmt)
        updated = result.scalar_one()
        return map_product_detail_model_to_entity(updated)

    async def delete(self, product_id: str) -> None:
        stmt = delete(Product).where(Product.id == product_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def set_active(self, product_id: str, is_active: bool) -> None:
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(is_active=is_active)
        )
        await self.session.execute(stmt)
        await self.session.flush()
