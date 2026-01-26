from typing import Protocol

from leaf_flow.domain.entities.support_topic import SupportTopicEntity


class SupportTopicReader(Protocol):
    async def get_by_user_telegram_id(
            self,
            user_telegram_id: int
    ) -> SupportTopicEntity | None:
        ...

    async def get_by_thread(
            self,
            admin_chat_id: int,
            thread_id: int
    ) -> SupportTopicEntity | None:
        ...


class SupportTopicWriter(Protocol):
    async def create(
            self,
            user_telegram_id: int,
            admin_chat_id: int,
            thread_id: int
    ) -> SupportTopicEntity:
        ...
