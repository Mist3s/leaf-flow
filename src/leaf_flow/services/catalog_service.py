from typing import Sequence

from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.domain.entities.product import ProductEntity


async def list_categories(uow: UoW) -> list[dict[str, str]]:
    return await uow.products.list_categories()


async def list_products(
    uow: UoW,
    category: str | None,
    search: str | None,
    limit: int,
    offset: int
) -> tuple[int, Sequence[ProductEntity]]:
    return await uow.products.get_list_products(category, search, limit, offset)


async def get_product(uow: UoW, product_id: str) -> ProductEntity | None:
    return await uow.products.get_with_variants(product_id)
