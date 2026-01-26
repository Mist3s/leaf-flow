from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class AuthTokens(BaseModel):
    accessToken: str = Field(validation_alias="access_token")
    refreshToken: str = Field(validation_alias="refresh_token")
    expiresIn: int = Field(validation_alias="expires_in")
    refreshExpiresIn: int = Field(validation_alias="refresh_expires_in")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserProfile(BaseModel):
    id: str
    telegramId: int | None = Field(validation_alias="telegram_id")
    email: str | None
    firstName: str = Field(validation_alias="first_name")
    lastName: str | None = Field(validation_alias="last_name")
    username: str | None
    languageCode: str | None = Field(validation_alias="language_code")
    photoUrl: str | None = Field(validation_alias="photo_url")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        # TODO: В модели id: int, схеме ответа id: str
        coerce_numbers_to_str=True
    )


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Пароль должен содержать минимум 8 символов")
    firstName: str
    lastName: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
