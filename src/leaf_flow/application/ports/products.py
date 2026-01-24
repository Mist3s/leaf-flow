from typing import Protocol, Sequence

from leaf_flow.domain.entities.product import (
    ProductEntity, ProductDetailEntity, ProductVariantEntity
)


class ProductsReader(Protocol):
    async def list_categories(self) -> list[dict[str, str]]:
        ...

    async def get_list_products(
        self,
        category_slug: str | None,
        search: str | None,
        limit: int,
        offset: int
    ) -> tuple[int, Sequence[ProductEntity]]:
        ...

    async def get_with_variants(
        self,
        product_id: str
    ) -> ProductDetailEntity | None:
        ...

    async def get_multiple_with_variants(
        self,
        product_ids: list[str]
    ) -> dict[str, ProductEntity]:
        ...

    async def get_for_product_variant(
            self,
            product_id: str,
            variant_id: str
    ) -> ProductVariantEntity | None:
        ...

    async def get_for_product_variants(
            self,
            keys: list[tuple[str, str]]
    ) -> dict[tuple[str, str], ProductVariantEntity]:
        ...
