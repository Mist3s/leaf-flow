from typing import Protocol

from leaf_flow.domain.entities.product import ProductImageEntity, ProductImageVariantEntity


class ImageReader(Protocol):
    async def get_by_id(
        self,
        image_id: int
    ) -> ProductImageEntity | None: ...

    async def get_by_product_id(
        self,
        product_id: str,
    ) -> list[ProductImageEntity]: ...


class ImageWriter(Protocol):
    async def create(
        self,
        product_id: str,
        title: str,
    ) -> ProductImageEntity: ...

    async def create_image_variant(
        self,
        image_id: int,
        variant: str,
        _format: str,
        storage_key: str,
        width: int,
        height: int,
        byte_size: int,
    ) -> ProductImageVariantEntity: ...

    async def delete(self, image_id: int) -> None: ...
