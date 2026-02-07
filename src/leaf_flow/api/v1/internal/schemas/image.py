"""Схемы для internal API изображений."""

from pydantic import BaseModel, Field


class CreateImageVariantRequest(BaseModel):
    """Запрос на создание варианта изображения."""
    
    variant: str = Field(..., description="Тип варианта: thumb, md, lg")
    storage_key: str = Field(..., description="Путь в S3")
    format: str = Field(..., description="Формат: webp, jpg, png")
    width: int = Field(..., ge=1, description="Ширина в пикселях")
    height: int = Field(..., ge=1, description="Высота в пикселях")
    byte_size: int = Field(..., ge=1, description="Размер в байтах")


class ImageVariantResponse(BaseModel):
    """Ответ с созданным вариантом."""
    
    id: int
    variant: str
    storage_key: str
    format: str
    width: int
    height: int
    byte_size: int
