"""
Outbox Processor — обрабатывает сообщения из таблицы outbox_messages.
"""
import asyncio
import logging

from leaf_flow.infrastructure.db.uow import get_uow, UoW
from leaf_flow.domain.entities.outbox import OutboxMessageEntity

logger = logging.getLogger(__name__)


class OutboxProcessor:
    """
    Процессор сообщений из outbox.
    
    Читает необработанные сообщения, вызывает соответствующие
    обработчики и отмечает сообщения как обработанные.
    """
    
    def __init__(
        self,
        handler_factory,
        batch_size: int = 100,
        max_attempts: int = 5,
        poll_interval: float = 1.0
    ):
        """
        Args:
            handler_factory: Фабрика обработчиков (EventHandlerFactory).
            batch_size: Размер пачки за одну итерацию.
            max_attempts: Максимальное количество попыток для сообщения.
            poll_interval: Интервал между проверками (секунды).
        """
        self._handler_factory = handler_factory
        self._batch_size = batch_size
        self._max_attempts = max_attempts
        self._poll_interval = poll_interval
        self._running = False
    
    async def process_batch(self) -> int:
        """
        Обработать пачку сообщений.
        
        Returns:
            Количество успешно обработанных сообщений.
        """
        processed_count = 0
        
        async for uow in get_uow():
            messages = await uow.outbox_reader.fetch_unprocessed(
                limit=self._batch_size,
                max_attempts=self._max_attempts
            )
            
            if not messages:
                return 0
            
            logger.debug(f"Fetched {len(messages)} messages to process")
            
            for msg in messages:
                success = await self._process_message(msg, uow)
                if success:
                    processed_count += 1
            
            await uow.commit()
        
        return processed_count
    
    async def _process_message(
        self,
        msg: OutboxMessageEntity,
        uow: UoW
    ) -> bool:
        """Обработать одно сообщение."""
        # msg.event содержит тип события (order.created, order.status_changed)
        event_type = msg.event
        if hasattr(event_type, 'value'):
            event_type = event_type.value
        
        handler = self._handler_factory.create(event_type, uow)
        
        if not handler:
            error = f"Unknown event_type: {event_type}"
            logger.error(f"{error}, message_id: {msg.id}")
            await uow.outbox_reader.mark_as_failed(msg.id, error)
            return False
        
        try:
            await handler.handle(msg.payload)
            await uow.outbox_reader.mark_as_processed(msg.id)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to process message {msg.id}: {e}")
            await uow.outbox_reader.mark_as_failed(msg.id, str(e)[:1000])
            return False
    
    async def run(self) -> None:
        """Запустить основной цикл обработки."""
        logger.info(
            f"OutboxProcessor started "
            f"(poll_interval={self._poll_interval}s, "
            f"batch_size={self._batch_size}, "
            f"max_attempts={self._max_attempts})"
        )
        
        self._running = True
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self._running:
            try:
                processed = await self.process_batch()
                
                if processed > 0:
                    logger.info(f"Processed {processed} outbox messages")
                
                consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                logger.exception(
                    f"OutboxProcessor error "
                    f"({consecutive_errors}/{max_consecutive_errors}): {e}"
                )
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical("Too many errors, increasing poll interval")
                    await asyncio.sleep(self._poll_interval * 10)
                    consecutive_errors = 0
            
            await asyncio.sleep(self._poll_interval)
    
    def stop(self) -> None:
        """Остановить процессор."""
        logger.info("OutboxProcessor stopping...")
        self._running = False
