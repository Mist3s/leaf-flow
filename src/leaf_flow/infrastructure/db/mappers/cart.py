from decimal import Decimal
from typing import Sequence

from leaf_flow.domain.entities.cart import CartItemEntity, CartEntity, CartDetailEntity
from leaf_flow.infrastructure.db.models import (
    CartItem as CartItemModel,
    Cart as CartModel
)
from leaf_flow.infrastructure.db.mappers.product import map_product_image_model_to_entity


def _calc_totals(items: Sequence[CartItemEntity]) -> tuple[int, Decimal]:
    total_count = 0
    total_price = Decimal("0.00")
    for it in items:
        total_count += it.quantity
        total_price += (it.price or Decimal("0.00")) * it.quantity
    return total_count, total_price


def map_cart_items_to_entities(
    items: Sequence[CartItemModel]
) -> Sequence[CartItemEntity]:
    entities: list[CartItemEntity] = []
    for it in items:
        images = [
            map_product_image_model_to_entity(img)
            for img in (it.product.images or [])
        ]
        entities.append(
            CartItemEntity(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                product_name=it.product.name,
                variant_weight=it.variant.weight,
                image=it.product.image,
                images=images,
            )
        )
    return entities


def map_cart_item_to_entities(
    item: CartItemModel
) -> CartItemEntity:
    images = [
        map_product_image_model_to_entity(img)
        for img in (item.product.images or [])
    ]
    return CartItemEntity(
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=item.quantity,
        price=item.price,
        product_name=item.product.name,
        variant_weight=item.variant.weight,
        image=item.product.image,
        images=images,
    )


def map_cart_to_entities(
    cart: CartModel
) -> CartEntity:
    return CartEntity(
        id=cart.id,
        user_id=cart.user_id,
        updated_at=cart.updated_at
    )


def map_cart_detail_to_entities(
    items: Sequence[CartItemModel]
) -> CartDetailEntity:
    items = map_cart_items_to_entities(items)
    total_count, total_price = _calc_totals(items)
    return CartDetailEntity(
        items=items,
        total_count=total_count,
        total_price=total_price
    )
