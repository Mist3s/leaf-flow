from dataclasses import dataclass


@dataclass(slots=True)
class UserEntity:
    id: int
    first_name: str
    telegram_id: int | None = None
    email: str = None
    last_name: str = None
    username: str = None
    language_code: str = None
    photo_url: str = None
    password_hash: str = None
