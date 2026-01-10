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


class UpdateProfileRequest(BaseModel):
    """Запрос на обновление профиля пользователя."""
    firstName: str | None = None
    lastName: str | None = None
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    """
    Запрос на изменение или создание пароля.
    
    - Если пароль уже установлен, требуется currentPassword
    - Если пароля нет (Telegram-пользователь), currentPassword не нужен
    """
    currentPassword: str | None = Field(None, description="Текущий пароль (обязателен, если пароль уже установлен)")
    newPassword: str = Field(..., min_length=8, description="Новый пароль (минимум 8 символов)")


class SetEmailRequest(BaseModel):
    """Запрос на установку email (для пользователей без email)."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Пароль для нового email-аккаунта")


