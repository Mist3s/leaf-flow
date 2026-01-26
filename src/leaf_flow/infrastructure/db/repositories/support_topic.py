from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.mappers.support_topic import map_support_topic_model_to_entity
from leaf_flow.infrastructure.db.models.support_topic import SupportTopic
from leaf_flow.infrastructure.db.repositories.base import Repository
from leaf_flow.application.ports.support_topic import SupportTopicReader, SupportTopicWriter
from leaf_flow.domain.entities.support_topic import SupportTopicEntity


class SupportTopicReaderRepository(Repository[SupportTopic], SupportTopicReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SupportTopic)

    async def get_by_user_telegram_id(
        self,
        user_telegram_id: int
    ) -> SupportTopicEntity | None:
        stmt = select(SupportTopic).where(
            SupportTopic.user_telegram_id == user_telegram_id
        )
        topic = (await self.session.execute(stmt)).scalar_one_or_none()

        if topic is None:
            return None

        return map_support_topic_model_to_entity(topic)

    async def get_by_thread(
        self,
        admin_chat_id: int,
        thread_id: int
    ) -> SupportTopicEntity | None:
        stmt = (
            select(SupportTopic).where(
                SupportTopic.admin_chat_id == admin_chat_id,
                SupportTopic.thread_id == thread_id,
            )
        )
        topic = (await self.session.execute(stmt)).scalar_one_or_none()

        if topic is None:
            return None

        return map_support_topic_model_to_entity(topic)


class SupportTopicWriterRepository(Repository[SupportTopic], SupportTopicWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SupportTopic)

    async def create(
        self,
        user_telegram_id: int,
        admin_chat_id: int,
        thread_id: int
    ) -> SupportTopicEntity:
        topic = SupportTopic(
            user_telegram_id=user_telegram_id,
            admin_chat_id=admin_chat_id,
            thread_id=thread_id
        )
        self.session.add(topic)
        await self.session.flush()
        return map_support_topic_model_to_entity(topic)
