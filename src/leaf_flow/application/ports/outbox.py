from typing import Protocol, Any, Sequence

from leaf_flow.domain.entities.outbox import OutboxMessageEntity


class OutboxWriter(Protocol):
    """Порт для записи сообщений в outbox."""

    async def add_message(
        self,
        event_type: str,
        payload: dict[str, Any],
        routing_key: str | None = None
    ) -> None:
        ...


class OutboxReader(Protocol):
    """Порт для чтения сообщений из outbox (для processor)."""

    async def fetch_unprocessed(
        self,
        limit: int = 100,
        max_attempts: int = 5
    ) -> Sequence[OutboxMessageEntity]:
        ...

    async def mark_as_processed(
        self,
        message_id: int
    ) -> None:
        ...

    async def mark_as_failed(
        self,
        message_id: int,
        error: str
    ) -> None:
        ...
