from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.outbox import OutboxWriter, OutboxReader
from leaf_flow.domain.entities.outbox import OutboxMessageEntity
from leaf_flow.infrastructure.db.mappers.outbox import map_outbox_massage_model_to_entity
from leaf_flow.infrastructure.db.models.outbox import OutboxMessage
from leaf_flow.infrastructure.db.repositories.base import Repository


class OutboxWriterRepository(Repository[OutboxMessage], OutboxWriter):
    """Репозиторий для записи сообщений в outbox."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, OutboxMessage)

    async def add_message(
        self,
        event_type: str,
        payload: dict[str, Any],
        routing_key: str | None = None
    ) -> None:
        """
        Добавить сообщение в outbox.

        Сообщение будет сохранено в той же транзакции,
        что и основная бизнес-операция.
        """
        message = OutboxMessage(
            event_type=event_type,
            payload=payload,
            routing_key=routing_key
        )
        self.session.add(message)


class OutboxReaderRepository(Repository[OutboxMessage], OutboxReader):
    """Репозиторий для чтения и обработки сообщений outbox."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, OutboxMessage)

    async def fetch_unprocessed(
        self,
        limit: int = 100,
        max_attempts: int = 5
    ) -> Sequence[OutboxMessageEntity]:
        """
        Получить необработанные сообщения.

        Использует SELECT ... FOR UPDATE SKIP LOCKED для
        безопасной параллельной обработки несколькими воркерами.
        """
        stmt = (
            select(OutboxMessage)
            .where(OutboxMessage.processed_at.is_(None))
            .where(OutboxMessage.attempts < max_attempts)
            .order_by(OutboxMessage.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        outbox_massages = (await self.session.execute(stmt)).scalars().all()
        return [
            map_outbox_massage_model_to_entity(outbox_massage)
            for outbox_massage in outbox_massages
        ]

    async def mark_as_processed(self, message_id: int) -> None:
        """Пометить сообщение как успешно обработанное."""
        stmt = (
            update(OutboxMessage)
            .where(OutboxMessage.id == message_id)
            .values(processed_at=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def mark_as_failed(self, message_id: int, error: str) -> None:
        """Увеличить счётчик попыток и записать ошибку."""
        stmt = (
            update(OutboxMessage)
            .where(OutboxMessage.id == message_id)
            .values(
                attempts=OutboxMessage.attempts + 1,
                last_error=error[:1000]  # Ограничиваем длину ошибки
            )
        )
        await self.session.execute(stmt)