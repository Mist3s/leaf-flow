from sqlalchemy import select
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.support_topic import SupportTopic
from leaf_flow.infrastructure.db.repositories.base import Repository


class SupportTopicRepository(Repository[SupportTopic]):
    def __init__(self, session: Session):
        super().__init__(session, SupportTopic)

    async def get_by_user_telegram_id(self, user_telegram_id: int) -> SupportTopic | None:
        result = await self.session.execute(
            select(SupportTopic).where(SupportTopic.user_telegram_id == user_telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_thread(self, admin_chat_id: int, thread_id: int) -> SupportTopic | None:
        result = await self.session.execute(
            select(SupportTopic).where(
                SupportTopic.admin_chat_id == admin_chat_id,
                SupportTopic.thread_id == thread_id,
            )
        )
        return result.scalar_one_or_none()







