from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SupportTopicEntity:
    id: int
    user_telegram_id: int
    admin_chat_id: int
    thread_id: int
    created_at: datetime
    updated_at: datetime
