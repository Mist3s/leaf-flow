from pydantic import BaseModel, EmailStr, Field


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
    telegramId: int | None = None
    email: str | None = None
    firstName: str
    lastName: str | None = None
    username: str | None = None
    languageCode: str | None = None
    photoUrl: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Пароль должен содержать минимум 8 символов")
    firstName: str
    lastName: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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


class AuthResponse(BaseModel):
    tokens: AuthTokens
    user: UserProfile


class RefreshRequest(BaseModel):
    refreshToken: str


class ErrorResponse(BaseModel):
    message: str
    code: str | None = None


