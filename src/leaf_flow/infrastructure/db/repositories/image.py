from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from leaf_flow.application.ports.image import ImageReader, ImageWriter
from leaf_flow.domain.entities.product import ProductImageEntity, ProductImageVariantEntity
from leaf_flow.infrastructure.db.mappers.product import (
    map_product_image_model_to_entity,
    map_product_image_variant_model_to_entity,
)
from leaf_flow.infrastructure.db.models.product import (
    ImageFormat,
    ImageVariant,
    ProductImage,
    ProductImageVariant,
)
from leaf_flow.infrastructure.db.repositories.base import Repository


class ImageReaderRepository(Repository[ProductImage], ImageReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductImage)

    async def get_by_id(
        self,
        image_id: int
    ) -> ProductImageEntity | None:
        image = (
            await self.session.execute(
                select(ProductImage)
                .where(
                    ProductImage.id == image_id
                )
                .options(
                    selectinload(
                        ProductImage.variants
                    )
                )
            )
        ).scalar_one_or_none()

        if not image:
            return None

        return map_product_image_model_to_entity(image)

    async def get_by_product_id(
        self,
        product_id: str,
    ) -> list[ProductImageEntity]:
        images = (
            await self.session.execute(
                select(ProductImage)
                .where(ProductImage.product_id == product_id)
                .options(selectinload(ProductImage.variants))
            )
        ).scalars().all()

        return [map_product_image_model_to_entity(image) for image in images]


class ImageWriterRepository(Repository[ProductImage], ImageWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductImage)

    async def create(
        self,
        product_id: str,
        title: str,
    ) -> ProductImageEntity:
        image = ProductImage(
            product_id=product_id,
            title=title,
        )

        self.session.add(image)
        await self.session.flush()

        return ProductImageEntity(
            id=image.id,
            product_id=image.product_id,
            title=image.title,
            image_url=image.image_url,
            is_active=image.is_active,
            sort_order=image.sort_order,
            variants=[]
        )

    async def create_image_variant(
        self,
        image_id: int,
        variant: str,
        _format: str,
        storage_key: str,
        width: int,
        height: int,
        byte_size: int,
    ) -> ProductImageVariantEntity:
        image_variant = ProductImageVariant(
            product_image_id=image_id,
            variant=ImageVariant(variant),
            format=ImageFormat(_format),
            storage_key=storage_key,
            width=width,
            height=height,
            byte_size=byte_size,
        )

        self.session.add(image_variant)
        await self.session.flush()
        return map_product_image_variant_model_to_entity(image_variant)

    async def delete(self, image_id: int) -> None:
        image = await self.session.get(ProductImage, image_id)
        if image:
            await self.session.delete(image)
            await self.session.flush()
