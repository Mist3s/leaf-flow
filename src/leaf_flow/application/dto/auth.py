from dataclasses import dataclass


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
