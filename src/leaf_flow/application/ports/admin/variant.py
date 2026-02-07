from typing import Protocol, Sequence

from leaf_flow.domain.entities.product import ProductVariantEntity


class AdminVariantReader(Protocol):
    async def get_by_id(self, variant_id: str) -> ProductVariantEntity | None: ...

    async def list_by_product(self, product_id: str) -> Sequence[ProductVariantEntity]: ...


class AdminVariantWriter(Protocol):
    async def create(
        self,
        id: str,
        product_id: str,
        weight: str,
        price: str,
        is_active: bool,
        sort_order: int,
    ) -> ProductVariantEntity: ...

    async def update(self, variant_id: str, **fields: object) -> ProductVariantEntity | None: ...

    async def delete(self, variant_id: str) -> None: ...

    async def set_active(self, variant_id: str, is_active: bool) -> None: ...
