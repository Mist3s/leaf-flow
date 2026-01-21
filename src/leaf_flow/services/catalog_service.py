from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.domain.entities.product import ProductEntity
from leaf_flow.domain.mappers.product import (
    map_product_model_to_entity,
    map_product_detail_model_to_entity
)


async def list_categories(uow: UoW) -> list[dict[str, str]]:
    return await uow.products.list_categories()


async def list_products(
    uow: UoW,
    category: str | None,
    search: str | None,
    limit: int,
    offset: int,
) -> tuple[int, list[ProductEntity]]:
    total, rows = await uow.products.search(category, search, limit, offset)
    return total, [map_product_model_to_entity(p) for p in rows]


async def get_product(uow: UoW, product_id: str) -> ProductEntity | None:
    p = await uow.products.get_with_variants(product_id)
    return map_product_detail_model_to_entity(p) if p else None
