from typing import Sequence

from leaf_flow.domain.entities.cart import CartItemEntity
from leaf_flow.infrastructure.db.models import CartItem as CartItemModel


def map_cart_items_to_entities(
    items: Sequence[CartItemModel]
) -> Sequence[CartItemEntity]:
    entities: list[CartItemEntity] = []
    for it in items:
        entities.append(
            CartItemEntity(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                product_name=it.product.name,
                variant_weight=it.variant.weight,
                image=it.product.image
            )
        )
    return entities
