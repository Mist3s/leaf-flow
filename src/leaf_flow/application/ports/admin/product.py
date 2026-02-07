from typing import Protocol, Sequence

from leaf_flow.domain.entities.product import ProductDetailEntity


class AdminProductReader(Protocol):
    async def get_by_id(self, product_id: str) -> ProductDetailEntity | None: ...

    async def list_products(
        self,
        search: str | None,
        category_slug: str | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[ProductDetailEntity]]: ...


class AdminProductWriter(Protocol):
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
    ) -> ProductDetailEntity: ...

    async def update(
        self,
        product_id: str,
        **fields: object,
    ) -> ProductDetailEntity | None: ...

    async def delete(self, product_id: str) -> None: ...

    async def set_active(self, product_id: str, is_active: bool) -> None: ...
