from pydantic import BaseModel, ConfigDict


class SupportTopicPublic(BaseModel):
    id: int
    user_telegram_id: int
    admin_chat_id: int
    thread_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SupportTopicEnsureRequest(BaseModel):
    user_telegram_id: int
    admin_chat_id: int
    thread_id: int


class SupportTopicByThreadResponse(BaseModel):
    user_telegram_id: int
    thread_id: int
    admin_chat_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
