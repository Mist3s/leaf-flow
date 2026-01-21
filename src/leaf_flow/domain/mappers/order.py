from leaf_flow.domain.entities.order import OrderItemEntity, OrderEntity
from leaf_flow.infrastructure.db.models import Order as OrderModel


def map_order_model_to_entity(order: OrderModel) -> OrderEntity:
    return OrderEntity(
        id=order.id,
        customer_name=order.customer_name,
        phone=order.phone,
        user_id=order.user_id,
        delivery=order.delivery.value,
        total=order.total,
        items=[
            OrderItemEntity(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
                product_name=it.product.name,
                variant_weight=it.variant.weight,
                image=it.product.image
            )
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status.value,
        created_at=order.created_at,
    )
