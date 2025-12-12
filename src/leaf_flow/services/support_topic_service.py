from leaf_flow.infrastructure.db.models.support_topics import SupportTopic
from leaf_flow.infrastructure.db.uow import UoW


async def get_by_telegram(user_telegram_id: int, uow: UoW) -> SupportTopic | None:
    return await uow.support_topics.get_by_user_telegram_id(user_telegram_id)


async def get_by_thread(admin_chat_id: int, thread_id: int, uow: UoW) -> SupportTopic | None:
    return await uow.support_topics.get_by_thread(admin_chat_id, thread_id)


async def ensure_support_topic(
    user_telegram_id: int,
    admin_chat_id: int,
    thread_id: int,
    uow: UoW,
) -> tuple[SupportTopic, bool]:
    existing_by_user = await uow.support_topics.get_by_user_telegram_id(user_telegram_id)
    if existing_by_user:
        if (existing_by_user.admin_chat_id, existing_by_user.thread_id) == (admin_chat_id, thread_id):
            return existing_by_user, False
        raise ValueError("CONFLICT_USER")

    existing_by_thread = await uow.support_topics.get_by_thread(admin_chat_id, thread_id)
    if existing_by_thread:
        raise ValueError("CONFLICT_THREAD")

    new_topic = SupportTopic(
        user_telegram_id=user_telegram_id,
        admin_chat_id=admin_chat_id,
        thread_id=thread_id,
    )
    await uow.support_topics.add(new_topic)
    await uow.flush()
    await uow.commit()
    return new_topic, True


