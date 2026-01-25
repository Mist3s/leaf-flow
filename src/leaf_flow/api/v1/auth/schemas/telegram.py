from pydantic import BaseModel


class TelegramInitRequest(BaseModel):
    initData: str
    appVersion: str | None = None


class TelegramLoginWidgetRequest(BaseModel):
    """
    Payload от Telegram Login Widget.
    https://core.telegram.org/widgets/login
    """
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class TelegramProfile(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
