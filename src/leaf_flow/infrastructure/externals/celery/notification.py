from leaf_flow.domain.entities.order import OrderEntity
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.application.dto.notification import NotificationsOrderEntity, OrderStatus
from leaf_flow.infrastructure.db.models import (
    SupportTopic as SupportTopicModel
)


def map_notifications_order_to_entity(
    order: OrderEntity,
    user: UserEntity,
    old_status: OrderStatus,
    status_comment: str | None = None,
    support_topic: SupportTopicModel = None,
) -> NotificationsOrderEntity:
    admin_chat_id = support_topic.admin_chat_id if support_topic else None
    thread_id = support_topic.thread_id if support_topic else None

    return NotificationsOrderEntity(
        order_id=order.id,
        telegram_id=user.telegram_id,
        old_status=old_status,
        new_status=order.status,
        comment=order.comment,
        phone=order.phone,
        customer_name=order.customer_name,
        total=order.total,
        delivery_method=order.delivery,
        email=user.email,
        address=order.address,
        status_comment=status_comment,
        admin_chat_id=admin_chat_id,
        thread_id=thread_id,
        created_at=order.created_at
    )
