"""Internal API для управления изображениями.

Используется Celery worker для сохранения вариантов изображений после обработки.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import uow_dep, require_internal_auth
from leaf_flow.api.v1.internal.schemas.image import (
    CreateImageVariantRequest,
    ImageVariantResponse,
)
from leaf_flow.infrastructure.db.uow import UoW


router = APIRouter(prefix="/internal/images", tags=["internal-images"])


@router.post(
    "/{image_id}/variants",
    response_model=ImageVariantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_image_variant(
    image_id: int,
    data: CreateImageVariantRequest,
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> ImageVariantResponse:
    """
    Создать вариант изображения.
    
    Используется Celery worker после обработки изображения через Cloudinary.
    Сохраняет метаданные варианта (thumb, md, lg) в БД.
    """
    # Проверяем существование изображения
    image = await uow.images_reader.get_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found"
        )
    
    # Создаём вариант
    variant = await uow.images_writer.create_image_variant(
        image_id=image_id,
        variant=data.variant,
        _format=data.format,
        storage_key=data.storage_key,
        width=data.width,
        height=data.height,
        byte_size=data.byte_size,
    )
    
    await uow.commit()
    
    return ImageVariantResponse(
        id=variant.id,
        variant=variant.variant,
        storage_key=variant.storage_key,
        format=variant.format,
        width=variant.width,
        height=variant.height,
        byte_size=variant.byte_size,
    )
