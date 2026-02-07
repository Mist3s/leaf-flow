"""
Доменные события изображений.

Создаётся при загрузке оригинального изображения для генерации
вариантов (thumb, md, lg).
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ImageUploadedEvent:
    """
    Событие загрузки изображения.
    
    Отправляется после успешной загрузки original варианта в S3.
    Обработчик создаёт дополнительные варианты (thumb, md, lg).
    
    Attributes:
        image_id: ID изображения в БД
        product_id: ID продукта
        original_url: Полный публичный URL оригинала (https://storage.../original.jpg)
        original_key: Ключ в S3 без домена (public/products/.../original.jpg)
        original_format: Формат файла (jpg, png, webp)
        original_width: Ширина в пикселях
        original_height: Высота в пикселях
    """
    image_id: int
    product_id: str
    original_url: str
    original_key: str
    original_format: str
    original_width: int
    original_height: int
    
    def to_payload(self) -> dict[str, Any]:
        """Сериализация в JSON-совместимый dict."""
        return {
            "image_id": self.image_id,
            "product_id": self.product_id,
            "original_url": self.original_url,
            "original_key": self.original_key,
            "original_format": self.original_format,
            "original_width": self.original_width,
            "original_height": self.original_height,
        }
    
    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ImageUploadedEvent":
        """Десериализация из payload."""
        return cls(
            image_id=payload["image_id"],
            product_id=payload["product_id"],
            original_url=payload["original_url"],
            original_key=payload["original_key"],
            original_format=payload["original_format"],
            original_width=payload["original_width"],
            original_height=payload["original_height"],
        )
