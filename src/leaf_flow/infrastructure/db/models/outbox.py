from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB

from leaf_flow.infrastructure.db.base import Base


class OutboxEventType(str, PyEnum):
    order_created = "order.created"
    order_status_changed = "order.status_changed"
    image_uploaded = "image.uploaded"


class OutboxMessage(Base):
    __tablename__ = "outbox_messages"

    id = Column(Integer, primary_key=True)
    event_type = Column(
        Enum(
            OutboxEventType,
            name="outbox_event_type",
            native_enum=True
        ),
        nullable=False,
        index=True
    )
    payload = Column(JSONB, nullable=False)
    routing_key = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
