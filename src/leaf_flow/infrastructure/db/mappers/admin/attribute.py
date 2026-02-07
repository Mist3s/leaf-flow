from leaf_flow.domain.entities.product import ProductAttributesValueEntity, ProductAttributesEntity
from leaf_flow.infrastructure.db.models.product import ProductAttributeValue, ProductAttribute


def map_attribute_value_to_entity(v: ProductAttributeValue) -> ProductAttributesValueEntity:
    return ProductAttributesValueEntity(
        id=v.id,
        attribute_id=v.attribute_id,
        name=v.name,
        slug=v.slug,
        sort_order=v.sort_order,
        is_active=v.is_active,
    )


def map_attribute_to_entity(attr: ProductAttribute) -> ProductAttributesEntity:
    return ProductAttributesEntity(
        id=attr.id,
        code=attr.code,
        name=attr.name,
        description=attr.description,
        sort_order=attr.sort_order,
        is_active=attr.is_active,
        created_at=attr.created_at,
        kind=attr.kind.value,
        ui_hint=attr.ui_hint.value,
        values=[map_attribute_value_to_entity(v) for v in (attr.values or [])],
    )
