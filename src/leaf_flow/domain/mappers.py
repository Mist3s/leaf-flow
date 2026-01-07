from decimal import Decimal
from typing import Sequence

from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.domain.entities.product import ProductEntity, ProductVariantEntity
from leaf_flow.domain.entities.cart import CartItemEntity
from leaf_flow.domain.entities.order import OrderEntity, OrderItemEntity
from leaf_flow.infrastructure.db.models.users import User as UserModel
from leaf_flow.infrastructure.db.models.products import Product as ProductModel, ProductVariant as ProductVariantModel
from leaf_flow.infrastructure.db.models.carts import CartItem as CartItemModel
from leaf_flow.infrastructure.db.models.orders import Order as OrderModel, OrderItem as OrderItemModel


def map_user_model_to_entity(user: UserModel) -> UserEntity:
    return UserEntity(
        id=user.id,
        first_name=user.first_name,
        telegram_id=user.telegram_id,
        email=user.email,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
        photo_url=user.photo_url,
    )


def map_product_variant_model_to_entity(variant: ProductVariantModel) -> ProductVariantEntity:
    return ProductVariantEntity(
        id=variant.id,
        weight=variant.weight,
        price=variant.price,
    )


def map_product_model_to_entity(product: ProductModel) -> ProductEntity:
    return ProductEntity(
        id=product.id,
        name=product.name,
        description=product.description,
        category_slug=product.category_slug,
        tags=list(product.tags or []),
        image=product.image,
        variants=[map_product_variant_model_to_entity(v) for v in getattr(product, "variants", [])],
    )


def map_cart_items_to_entities(items: Sequence[CartItemModel]) -> list[CartItemEntity]:
    entities: list[CartItemEntity] = []
    for it in items:
        entities.append(
            CartItemEntity(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                price=it.price,
            )
        )
    return entities


def map_order_model_to_entity(order: OrderModel, items: Sequence[OrderItemModel]) -> OrderEntity:
    return OrderEntity(
        id=order.id,
        customer_name=order.customer_name,
        phone=order.phone,
        delivery=order.delivery.value,  # type: ignore[assignment]
        total=order.total,
        items=[
            OrderItemEntity(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
            )
            for it in items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status.value,  # type: ignore[assignment]
        created_at=order.created_at,
    )


