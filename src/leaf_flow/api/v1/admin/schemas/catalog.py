from typing import Literal

from pydantic import BaseModel, ConfigDict

ImageVariant = Literal["original", "thumb", "md", "lg"]
ImageFormat = Literal["jpg", "jpeg", "png", "webp"]

class ProductImageVariant(BaseModel):
    id: int
    product_image_id: int
    variant: ImageVariant
    format: ImageFormat
    storage_key: str
    width: int
    height: int
    byte_size: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProductImage(BaseModel):
    id: int
    product_id: str
    title: str
    is_active: bool
    sort_order: int
    variants: list[ProductImageVariant]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
