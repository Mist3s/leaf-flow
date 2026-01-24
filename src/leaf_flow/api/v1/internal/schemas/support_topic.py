from pydantic import BaseModel


class SupportTopicPublic(BaseModel):
    id: int
    user_telegram_id: int
    admin_chat_id: int
    thread_id: int


class SupportTopicEnsureRequest(BaseModel):
    user_telegram_id: int
    admin_chat_id: int
    thread_id: int


class SupportTopicByThreadResponse(BaseModel):
    user_telegram_id: int
    thread_id: int
    admin_chat_id: int






