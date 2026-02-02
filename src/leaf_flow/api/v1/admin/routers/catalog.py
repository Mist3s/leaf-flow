from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from leaf_flow.api.deps import admin_uow_dep, get_object_storage, require_admin_auth
from leaf_flow.api.v1.admin.schemas.catalog import ProductImage
from leaf_flow.infrastructure.db.admin_uow import AdminUoW
from leaf_flow.infrastructure.externals.s3.storage import S3ObjectStorage
from leaf_flow.services.admin import images_service
from leaf_flow.services.admin.images_service import ImageProcessingError


router = APIRouter(prefix="/catalog")


@router.post("/images", response_model=ProductImage, status_code=status.HTTP_201_CREATED)
async def create_image(
    file: UploadFile,
    product_id: str,
    title: str = "",
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> ProductImage:
    """Загрузить изображение продукта."""
    try:
        image = await images_service.create_image(
            file=file.file,
            filename=file.filename or "image.bin",
            content_type=file.content_type,
            product_id=product_id,
            title=title,
            uow=uow,
            storage=storage,
        )
    except ImageProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return ProductImage.model_validate(image, from_attributes=True)


@router.get("/images/{image_id}", response_model=ProductImage)
async def get_image(
    image_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ProductImage:
    """Получить изображение по ID."""
    image = await images_service.get_image(image_id, uow)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Изображение не найдено",
        )
    return ProductImage.model_validate(image, from_attributes=True)


@router.get("/products/{product_id}/images", response_model=list[ProductImage])
async def list_product_images(
    product_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[ProductImage]:
    """Получить все изображения продукта."""
    images = await images_service.list_images_by_product(product_id, uow)
    return [ProductImage.model_validate(img, from_attributes=True) for img in images]


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> None:
    """Удалить изображение."""
    deleted = await images_service.delete_image(image_id, uow, storage)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Изображение не найдено",
        )
