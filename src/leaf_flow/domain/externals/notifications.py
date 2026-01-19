from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Any

DeliveryMethod = Literal["pickup", "courier", "cdek"]
OrderStatus = Literal["created", "processing", "paid", "fulfilled", "cancelled"]


@dataclass(slots=True)
class NotificationsOrderEntity:
    order_id: str
    telegram_id: int | None
    old_status: OrderStatus
    new_status: OrderStatus
    comment: str | None
    phone: str
    customer_name: str
    total: Decimal
    delivery_method: DeliveryMethod
    email: str | None = None
    address: str | None = None
    status_comment: str | None = None
    admin_chat_id: int | None = None
    thread_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        """
        JSON-friendly dict for Celery.
        - Decimal -> str
        """
        return {
            "order_id": self.order_id,
            "telegram_id": self.telegram_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "comment": self.comment,
            "phone": self.phone,
            "customer_name": self.customer_name,
            "total": str(self.total),
            "delivery_method": self.delivery_method,
            "email": self.email,
            "address": self.address,
            "status_comment": self.status_comment,
            "admin_chat_id": self.admin_chat_id,
            "thread_id": self.thread_id,
        }