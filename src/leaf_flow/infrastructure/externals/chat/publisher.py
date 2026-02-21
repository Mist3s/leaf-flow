import logging
from typing import Any

from redis.asyncio import Redis

from leaf_flow.config import settings

logger = logging.getLogger(__name__)


class ChatEventPublisher:
    """Издет системные события в Redis Stream сервиса чата."""

    def __init__(self, redis_url: str = settings.CHAT_REDIS_URL, stream_name: str = settings.LEAF_EVENTS_STREAM):
        self._redis_url = redis_url
        self._stream_name = stream_name
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info(f"Connected to Chat Redis at {self._redis_url}")
        return self._redis

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """
        Публикует событие в Redis Stream.
        Хеши и вложенные структуры не поддерживаются, поэтому
        все значения приводятся к строке.
        """
        try:
            redis = await self._get_redis()
            
            # Redis Stream принимает только строки для ключей и значений
            stringified_fields = {"event_type": event_type}
            stringified_fields.update(
                {str(k): str(v) for k, v in payload.items() if v is not None}
            )

            message_id = await redis.xadd(self._stream_name, stringified_fields)
            logger.debug(
                f"Published chat event '{event_type}' "
                f"with payload {stringified_fields} (msg id: {message_id})"
            )
        except Exception as e:
            logger.error(f"Failed to publish chat event '{event_type}': {e}")
            raise
    
    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()


# Singleton экземпляр для переиспользования
chat_event_publisher = ChatEventPublisher()
