from dataclasses import dataclass


@dataclass(slots=True)
class UserEntity:
    id: int
    first_name: str
    telegram_id: int | None = None
    email: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
    password_hash: str | None = None
