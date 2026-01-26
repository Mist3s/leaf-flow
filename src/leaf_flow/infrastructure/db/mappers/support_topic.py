from leaf_flow.domain.entities.support_topic import SupportTopicEntity
from leaf_flow.infrastructure.db.models.support_topic import SupportTopic as SupportTopicModel


def map_support_topic_model_to_entity(
    support_topic: SupportTopicModel
) -> SupportTopicEntity:
    return SupportTopicEntity(
        id=support_topic.id,
        user_telegram_id=support_topic.user_telegram_id,
        admin_chat_id=support_topic.admin_chat_id,
        thread_id=support_topic.thread_id,
        created_at=support_topic.created_at,
        updated_at=support_topic.updated_at
    )
