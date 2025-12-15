from decimal import Decimal

from leaf_flow.domain.entities.product import ProductEntity, ProductVariantEntity
from leaf_flow.domain.mappers import map_product_model_to_entity, map_product_variant_model_to_entity
from leaf_flow.infrastructure.db.models.products import Product, ProductVariant
from leaf_flow.infrastructure.db.uow import UoW


async def _ensure_category_exists(category_slug: str, uow: UoW) -> None:
    category = await uow.categories.get_by_slug(category_slug)
    if not category:
        raise ValueError("CATEGORY_NOT_FOUND")


async def create_product(
    *,
    product_id: str,
    name: str,
    description: str,
    category_slug: str,
    tags: list[str],
    image: str,
    uow: UoW,
) -> ProductEntity:
    existing = await uow.products.get(product_id)
    if existing:
        raise ValueError("PRODUCT_EXISTS")

    await _ensure_category_exists(category_slug, uow)

    product = Product(
        id=product_id,
        name=name,
        description=description,
        category_slug=category_slug,
        tags=tags,
        image=image,
    )
    await uow.products.add(product)
    await uow.flush()
    await uow.commit()
    return map_product_model_to_entity(product)


async def update_product(
    product_id: str,
    *,
    name: str | None,
    description: str | None,
    category_slug: str | None,
    tags: list[str] | None,
    image: str | None,
    uow: UoW,
) -> ProductEntity:
    product = await uow.products.get_with_variants(product_id)
    if not product:
        raise ValueError("PRODUCT_NOT_FOUND")

    if category_slug:
        await _ensure_category_exists(category_slug, uow)
        product.category_slug = category_slug

    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if tags is not None:
        product.tags = tags
    if image is not None:
        product.image = image

    await uow.commit()
    return map_product_model_to_entity(product)


async def add_product_variant(
    product_id: str,
    *,
    variant_id: str,
    weight: str,
    price: Decimal,
    uow: UoW,
) -> ProductVariantEntity:
    product = await uow.products.get_with_variants(product_id)
    if not product:
        raise ValueError("PRODUCT_NOT_FOUND")

    existing_variant = await uow.product_variants.get_for_product(product_id, variant_id)
    if existing_variant:
        raise ValueError("VARIANT_EXISTS")

    for variant in product.variants:
        if variant.weight == weight:
            raise ValueError("VARIANT_WEIGHT_CONFLICT")

    new_variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        weight=weight,
        price=price,
    )
    await uow.product_variants.add(new_variant)
    await uow.flush()
    await uow.commit()
    return map_product_variant_model_to_entity(new_variant)


async def update_product_variant(
    product_id: str,
    variant_id: str,
    *,
    weight: str | None,
    price: Decimal | None = None,
    uow: UoW,
) -> ProductVariantEntity:
    product = await uow.products.get_with_variants(product_id)
    if not product:
        raise ValueError("PRODUCT_NOT_FOUND")

    variant = next((v for v in product.variants if v.id == variant_id), None)
    if not variant:
        raise ValueError("VARIANT_NOT_FOUND")

    if weight is not None:
        for existing_variant in product.variants:
            if existing_variant.weight == weight and existing_variant.id != variant_id:
                raise ValueError("VARIANT_WEIGHT_CONFLICT")
        variant.weight = weight
    if price is not None:
        variant.price = price

    await uow.commit()
    return map_product_variant_model_to_entity(variant)
