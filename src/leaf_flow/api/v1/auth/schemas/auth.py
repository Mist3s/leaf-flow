from pydantic import BaseModel


class TelegramInitRequest(BaseModel):
    initData: str
    appVersion: str | None = None


class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    refreshExpiresIn: int


class UserProfile(BaseModel):
    id: str
    telegramId: int
    firstName: str
    lastName: str | None = None
    username: str | None = None
    languageCode: str | None = None
    photoUrl: str | None = None


class AuthResponse(BaseModel):
    tokens: AuthTokens
    user: UserProfile


class RefreshRequest(BaseModel):
    refreshToken: str


class ErrorResponse(BaseModel):
    message: str
    code: str | None = None


