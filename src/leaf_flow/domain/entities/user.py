from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UserEntity:
    id: int
    first_name: str
    telegram_id: int | None = None
    email: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    photo_url: Optional[str] = None


