import asyncio
from leaf_flow.infrastructure.db.uow import get_uow

async def insert_test_message():
    async for uow in get_uow():
        await uow.outbox_writer.add_message(
            event_type='chat.order.created',
            payload={'order_id': 999, 'user_id': 888}
        )
        await uow.commit()
        print('Test chat message inserted')

asyncio.run(insert_test_message())
