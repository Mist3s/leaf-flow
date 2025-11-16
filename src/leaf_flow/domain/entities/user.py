from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UserEntity:
    id: int
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    photo_url: Optional[str] = None


