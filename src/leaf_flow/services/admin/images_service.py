import io
from typing import IO, Sequence

import imageio.v3 as imageio

from leaf_flow.domain.entities.product import ProductImageEntity
from leaf_flow.infrastructure.db.admin_uow import AdminUoW
from leaf_flow.infrastructure.externals.s3.storage import S3ObjectStorage


class ImageProcessingError(Exception):
    """Ошибка обработки изображения."""


def get_image_dimensions(data: bytes) -> tuple[int, int]:
    """Получить размеры изображения (width, height).

    Raises:
        ImageProcessingError: если не удалось прочитать изображение.
    """
    try:
        img = imageio.imread(io.BytesIO(data))
        return int(img.shape[1]), int(img.shape[0])  # width, height
    except Exception as ex:
        raise ImageProcessingError(f"Не удалось определить размеры изображения: {ex}") from ex


async def create_image(
    file: IO[bytes],
    filename: str,
    content_type: str | None,
    product_id: str,
    title: str,
    uow: AdminUoW,
    storage: S3ObjectStorage,
) -> ProductImageEntity:
    """Создать изображение продукта и загрузить в S3.

    Args:
        file: файловый объект с изображением
        filename: оригинальное имя файла
        content_type: MIME-тип файла
        product_id: ID продукта
        title: заголовок изображения
        uow: Unit of Work
        storage: S3 хранилище

    Returns:
        Созданная сущность ProductImageEntity

    Raises:
        ImageProcessingError: если не удалось обработать изображение.
    """
    image = await uow.images_writer.create(
        product_id=product_id,
        title=title,
    )

    ext = filename.rsplit(".", 1)[-1].lower() if filename else "bin"
    original_key = f"public/products/{product_id}/{image.id}/original.{ext}"

    content = file.read()
    byte_size = len(content)

    width, height = get_image_dimensions(content)

    await uow.images_writer.create_image_variant(
        image_id=image.id,
        variant="original",
        storage_key=original_key,
        _format=ext,
        width=width,
        height=height,
        byte_size=byte_size,
    )

    storage.put_bytes(
        key=original_key,
        data=content,
        content_type=content_type or "application/octet-stream",
    )

    await uow.commit()

    return await get_image(image.id, uow) or image


async def get_image(image_id: int, uow: AdminUoW) -> ProductImageEntity | None:
    """Получить изображение по ID.

    Args:
        image_id: ID изображения
        uow: Unit of Work

    Returns:
        Сущность изображения или None
    """
    return await uow.images_reader.get_by_id(image_id)


async def list_images_by_product(
    product_id: str,
    uow: AdminUoW,
) -> Sequence[ProductImageEntity]:
    """Получить все изображения продукта.

    Args:
        product_id: ID продукта
        uow: Unit of Work

    Returns:
        Список изображений продукта
    """
    return await uow.images_reader.get_by_product_id(product_id)


async def delete_image(
    image_id: int,
    uow: AdminUoW,
    storage: S3ObjectStorage,
) -> bool:
    """Удалить изображение и все его варианты из БД и S3.

    Args:
        image_id: ID изображения
        uow: Unit of Work
        storage: S3 хранилище

    Returns:
        True если изображение было удалено, False если не найдено
    """
    image = await uow.images_reader.get_by_id(image_id)
    if not image:
        return False

    # Удаляем файлы из S3
    for variant in image.variants:
        try:
            storage.delete(key=variant.storage_key)
        except Exception:
            # Логируем, но не прерываем удаление
            pass

    # Удаляем запись из БД
    await uow.images_writer.delete(image_id)
    await uow.commit()

    return True
