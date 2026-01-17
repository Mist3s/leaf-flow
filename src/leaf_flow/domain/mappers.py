from typing import Iterable, Sequence
from collections import defaultdict

from sqlalchemy.engine import Row

from leaf_flow.domain.entities.product import (
    ProductEntity,
    ProductDetailEntity,
    ProductVariantEntity,
    ProductAttributesEntity,
    ProductAttributesValueEntity,
    BrewProfileEntity
)
from leaf_flow.domain.entities.reviews import (
    ExternalReviewEntity, ReviewPlatformStatsEntity
)
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.domain.entities.cart import CartItemEntity
from leaf_flow.domain.entities.order import (
    OrderEntity, OrderItemEntity
)
from leaf_flow.infrastructure.db.models.reviews import (
    ExternalReview as ExternalReviewModel,
    PlatformEnum as PlatformEnumDB,
)
from leaf_flow.infrastructure.db.models.users import (
    User as UserModel
)
from leaf_flow.infrastructure.db.models.products import (
    Product as ProductModel,
    ProductVariant as ProductVariantModel,
    ProductAttribute as ProductAttributeModel,
    ProductAttributeValue as ProductAttributeValueModel,
)
from leaf_flow.infrastructure.db.models.carts import (
    CartItem as CartItemModel
)
from leaf_flow.infrastructure.db.models.orders import (
    Order as OrderModel,
    OrderItem as OrderItemModel
)


def map_external_review_model_to_entity(
    external_review: ExternalReviewModel
) -> ExternalReviewEntity:
    return ExternalReviewEntity(
        id=external_review.id,
        platform=external_review.platform.value,
        author=external_review.author,
        rating=external_review.rating,
        text=external_review.text,
        date=external_review.date
    )


def map_review_stats_model_to_entity(row: Row) -> ReviewPlatformStatsEntity:
    return ReviewPlatformStatsEntity(
        platform=row.platform.value,
        avg_rating=row.avg_rating,
        reviews_count=row.reviews_count
    )


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
    # variants
    variants = [map_product_variant_model_to_entity(v) for v in getattr(product, "variants", [])]

    # attribute values (выбранные значения товара), сгруппированные по attribute
    # Ожидается, что product.attribute_values — список ProductAttributeValueModel
    values: Iterable[ProductAttributeValueModel] = getattr(product, "attribute_values", []) or []

    grouped: dict[int, dict] = defaultdict(lambda: {"attribute": None, "values": []})

    for v in values:
        attr: ProductAttributeModel | None = getattr(v, "attribute", None)
        if attr is None:
            # если relationship attribute не загружен — атрибут не собрать корректно
            # лучше обеспечить eager load (см. ниже)
            continue

        g = grouped[attr.id]
        g["attribute"] = attr
        g["values"].append(v)

    # сортировка атрибутов и значений
    attributes: list[ProductAttributesEntity] = []
    for attr_id, pack in grouped.items():
        attr: ProductAttributeModel = pack["attribute"]
        vals: list[ProductAttributeValueModel] = pack["values"]

        # если нужно показывать только активные — раскомментируйте:
        # if not attr.is_active:
        #     continue
        # vals = [v for v in vals if v.is_active]

        vals_sorted = sorted(vals, key=lambda x: (x.sort_order, x.id))

        attributes.append(
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
                values=[map_product_attribute_value_model_to_entity(v) for v in vals_sorted],
            )
        )

    attributes.sort(key=lambda a: (a.sort_order, a.code))

    return ProductDetailEntity(
        id=product.id,
        name=product.name,
        description=product.description,
        category_slug=product.category_slug,
        tags=list(product.tags or []),
        image=product.image,
        variants=sorted(variants, key=lambda v: (v.sort_order, v.weight, v.id)),
        product_type_code=product.product_type_code,
        attribute_values=attributes,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        sort_order=getattr(product, "sort_order", 0),
        brew_profiles=sorted(
            [map_brew_profile_model_to_entity(x) for x in getattr(product, "brew_profiles", [])],
            key=lambda x: (x.sort_order, x.id),
        ),
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
        user_id=order.user_id,
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


def map_product_model_to_entity(product: ProductModel) -> ProductEntity:
    variants = [
        map_product_variant_model_to_entity(v) for v in getattr(product, "variants", [])
    ]

    return ProductEntity(
        id=product.id,
        name=product.name,
        category_slug=product.category_slug,
        tags=list(product.tags or []),
        image=product.image,
        variants=sorted(variants, key=lambda v: (v.sort_order, v.weight, v.id)),
        product_type_code=product.product_type_code,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        sort_order=getattr(product, "sort_order", 0)
    )
