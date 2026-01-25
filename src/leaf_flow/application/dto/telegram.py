from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramUserData:
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    language_code: str | None
    photo_url: str | None
