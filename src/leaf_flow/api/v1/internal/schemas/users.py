from pydantic import BaseModel


class InternalUserPublic(BaseModel):
    id: str
    telegramId: int
    firstName: str | None = None
    lastName: str | None = None
    username: str | None = None
    languageCode: str | None = None
    photoUrl: str | None = None


class TelegramBotRegisterRequest(BaseModel):
    telegramId: int
    firstName: str
    lastName: str | None = None
    username: str | None = None
    languageCode: str | None = None
    photoUrl: str | None = None
