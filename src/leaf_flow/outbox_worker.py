"""
Точка входа для Outbox Processor.

Запуск:
    python -m leaf_flow.outbox_worker
"""
import asyncio
import logging

from leaf_flow.config import settings
from leaf_flow.infrastructure.outbox.processor import OutboxProcessor
from leaf_flow.services.notification.order_handlers import EventHandlerFactory


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.OUTBOX_LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    processor = OutboxProcessor(
        handler_factory=EventHandlerFactory,
        batch_size=settings.OUTBOX_BATCH_SIZE,
        max_attempts=settings.OUTBOX_MAX_ATTEMPTS,
        poll_interval=settings.OUTBOX_POLL_INTERVAL
    )

    asyncio.run(processor.run())


if __name__ == "__main__":
    main()
