from dataclasses import dataclass
from datetime import datetime
from typing import Literal


OutboxEventType = Literal[
    "order.created",
    "order.status_changed"
]


@dataclass(frozen=True)
class OutboxMessageEntity:
    id: int
    event: OutboxEventType
    payload: dict
    routing_key: str
    created_at: datetime
    processed_at: datetime
    attempts: int
    last_error: str
