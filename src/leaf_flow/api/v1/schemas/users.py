from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = Field(None, max_length=120)

class UserUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)
