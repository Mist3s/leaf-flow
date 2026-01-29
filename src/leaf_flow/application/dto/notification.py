from dataclasses import dataclass
from datetime import datetime
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
    created_at: datetime
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
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }
    
    @classmethod
    def from_outbox_payload(
        cls,
        payload: dict[str, Any],
        telegram_id: int | None,
        email: str | None,
        admin_chat_id: int | None,
        thread_id: int | None,
        old_status: OrderStatus,
        new_status: OrderStatus,
        status_comment: str | None = None,
    ) -> "NotificationsOrderEntity":
        """
        Создать entity из payload события outbox и данных пользователя.
        
        Args:
            payload: Данные заказа из outbox (order_id, phone, customer_name, etc.)
            telegram_id: Telegram ID пользователя
            email: Email пользователя
            admin_chat_id: ID чата администратора
            thread_id: ID треда в чате
            old_status: Старый статус заказа
            new_status: Новый статус заказа
            status_comment: Комментарий к изменению статуса
        """
        return cls(
            order_id=payload["order_id"],
            telegram_id=telegram_id,
            old_status=old_status,
            new_status=new_status,
            comment=payload.get("comment"),
            phone=payload["phone"],
            customer_name=payload["customer_name"],
            total=Decimal(payload["total"]),
            delivery_method=payload["delivery"],
            email=email,
            address=payload.get("address"),
            status_comment=status_comment,
            admin_chat_id=admin_chat_id,
            thread_id=thread_id,
            created_at=datetime.fromisoformat(payload["created_at"])
        )
