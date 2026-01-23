from leaf_flow_core.models.support_topics import SupportTopic as SupportTopicModel
from leaf_flow_core.models.orders import Order as OrderModel
from leaf_flow_core.models.users import User as UserModel
from leaf_flow_core.enums.order import OrderStatusEnum as OrderStatusEnumDB
from leaf_flow_core.entities.notifications import NotificationsOrderEntity


def map_notifications_order_to_entity(
    order: OrderModel,
    user: UserModel,
    old_status: OrderStatusEnumDB,
    status_comment: str | None = None,
    support_topic: SupportTopicModel = None,
) -> NotificationsOrderEntity:
    admin_chat_id = support_topic.admin_chat_id if support_topic else None
    thread_id = support_topic.thread_id if support_topic else None

    return NotificationsOrderEntity(
        order_id=order.id,
        telegram_id=user.telegram_id,
        old_status=old_status.value,
        new_status=order.status.value,
        comment=order.comment,
        phone=order.phone,
        customer_name=order.customer_name,
        total=order.total,
        delivery_method=order.delivery.value,
        email=user.email,
        address=order.address,
        status_comment=status_comment,
        admin_chat_id=admin_chat_id,
        thread_id=thread_id,
        created_at=order.created_at
    )
