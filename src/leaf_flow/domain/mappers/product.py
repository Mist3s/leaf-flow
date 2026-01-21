from itertools import groupby

from leaf_flow.domain.entities.product import (
    ProductEntity,
    ProductDetailEntity,
    ProductVariantEntity,
    ProductAttributesEntity,
    ProductAttributesValueEntity,
    BrewProfileEntity,
    ProductImageEntity
)
from leaf_flow.infrastructure.db.models.products import (
    Product as ProductModel,
    ProductVariant as ProductVariantModel,
    ProductAttributeValue as ProductAttributeValueModel,
    ProductImage as ProductImageModel
)


def map_product_image_model_to_entity(
        img: ProductImageModel
) -> ProductImageEntity:
    return ProductImageEntity(
        id=img.id,
        product_id=img.product_id,
        title=img.title,
        image_url=img.image_url,
        is_active=img.is_active,
        sort_order=img.sort_order,
    )


def map_product_selected_attributes(
    values: list[ProductAttributeValueModel]
) -> list[ProductAttributesEntity]:
    values = list(values or [])

    # сортировка так, чтобы значения одного атрибута шли подряд
    values.sort(
        key=lambda v: (
            v.attribute.sort_order,
            v.attribute.code,
            v.attribute.id,
            v.sort_order,
            v.id,
        )
    )

    result: list[ProductAttributesEntity] = []

    for attr_id, group in groupby(values, key=lambda v: v.attribute.id):
        group_list = list(group)
        attr = group_list[0].attribute

        if attr is None:
            raise RuntimeError(
                "ProductAttributeValue.attribute is not loaded (missing selectinload)."
            )

        result.append(
            ProductAttributesEntity(
                id=attr.id,
                code=attr.code,
                name=attr.name,
                description=attr.description,
                sort_order=attr.sort_order,
                is_active=attr.is_active,
                created_at=attr.created_at,
                kind=_enum_to_str(attr.kind),
                ui_hint=_enum_to_str(attr.ui_hint),
                values=[map_product_attribute_value_model_to_entity(v) for v in group_list],
            )
        )

    # если хочешь — отдельно сортировать атрибуты (обычно уже отсортированы ключом выше)
    result.sort(key=lambda a: (a.sort_order, a.code, a.id))
    return result


def map_product_variant_model_to_entity(
    variant: ProductVariantModel
) -> ProductVariantEntity:
    return ProductVariantEntity(
        id=variant.id,
        weight=variant.weight,
        price=variant.price,
        is_active=variant.is_active,
        created_at=variant.created_at,
        updated_at=variant.updated_at,
        sort_order=variant.sort_order,
    )


def map_product_attribute_value_model_to_entity(
    v: ProductAttributeValueModel
) -> ProductAttributesValueEntity:
    return ProductAttributesValueEntity(
        id=v.id,
        attribute_id=v.attribute_id,
        name=v.name,
        slug=v.slug,
        sort_order=v.sort_order,
        is_active=v.is_active,
    )


def _enum_to_str(x):
    # Поддержка SQLAlchemy Enum: AttributeKind/UIHint могут быть enum с .value
    return getattr(x, "value", x)

def map_brew_profile_model_to_entity(p) -> BrewProfileEntity:
    return BrewProfileEntity(
        id=p.id,
        method=p.method,
        teaware=p.teaware,
        temperature=p.temperature,
        brew_time=p.brew_time,
        weight=p.weight,
        note=p.note,
        sort_order=p.sort_order,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def map_product_detail_model_to_entity(product: ProductModel) -> ProductDetailEntity:
    variants = sorted(
        (map_product_variant_model_to_entity(v) for v in (product.variants or [])),
        key=lambda v: (v.sort_order, v.weight, v.id),
    )

    brew_profiles = sorted(
        (map_brew_profile_model_to_entity(p) for p in (product.brew_profiles or [])),
        key=lambda x: (x.sort_order, x.id),
    )

    attributes = map_product_selected_attributes(product.attribute_values or [])

    images = [map_product_image_model_to_entity(i) for i in (product.images or [])]

    return ProductDetailEntity(
        id=product.id,
        name=product.name,
        description=product.description,
        category_slug=product.category_slug,
        tags=list(product.tags or []),
        image=product.image,
        variants=variants,
        product_type_code=product.product_type_code,
        attribute_values=attributes,
        brew_profiles=brew_profiles,
        images=images,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        sort_order=getattr(product, "sort_order", 0),
    )


def map_product_model_to_entity(product: ProductModel) -> ProductEntity:
    variants = sorted(
        (map_product_variant_model_to_entity(v) for v in (product.variants or [])),
        key=lambda v: (v.sort_order, v.weight, v.id),
    )

    return ProductEntity(
        id=product.id,
        name=product.name,
        category_slug=product.category_slug,
        tags=list(product.tags or []),
        image=product.image,
        variants=variants,
        product_type_code=product.product_type_code,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        sort_order=getattr(product, "sort_order", 0)
    )
