from leaf_flow.domain.entities.outbox import OutboxMessageEntity
from leaf_flow.infrastructure.db.models.outbox import (
    OutboxMessage as OutboxMessageModel
)


def map_outbox_massage_model_to_entity(
        outbox_massage: OutboxMessageModel
) -> OutboxMessageEntity:
    return OutboxMessageEntity(
        id=outbox_massage.id,
        event=outbox_massage.event_type,
        payload=outbox_massage.payload,
        routing_key=outbox_massage.routing_key,
        created_at=outbox_massage.created_at,
        processed_at=outbox_massage.processed_at,
        attempts=outbox_massage.attempts,
        last_error=outbox_massage.last_error
    )
