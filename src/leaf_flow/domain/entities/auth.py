from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RefreshTokenEntity:
    id: int | None
    user_id: int
    token: str
    expires_at: datetime
    revoked: bool
    revoked_at: datetime | None = None
