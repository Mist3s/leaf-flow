import asyncio
import io
import logging
from typing import IO, Sequence

import imageio.v3 as imageio

from leaf_flow.domain.entities.product import ProductImageEntity
from leaf_flow.infrastructure.db.admin_uow import AdminUoW
from leaf_flow.infrastructure.externals.s3.storage import S3ObjectStorage


logger = logging.getLogger(__name__)


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


async def _upload_to_s3(
    storage: S3ObjectStorage,
    key: str,
    data: bytes,
    content_type: str,
) -> None:
    """Загрузить данные в S3 асинхронно через thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: storage.put_bytes(key=key, data=data, content_type=content_type),
    )


async def _delete_from_s3(storage: S3ObjectStorage, key: str) -> None:
    """Удалить файл из S3 асинхронно через thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: storage.delete(key=key))


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
    content = file.read()
    byte_size = len(content)

    # Валидируем изображение до записи в БД
    width, height = get_image_dimensions(content)

    ext = filename.rsplit(".", 1)[-1].lower() if filename else "bin"

    try:
        image = await uow.images_writer.create(
            product_id=product_id,
            title=title,
        )

        original_key = f"public/products/{product_id}/{image.id}/original.{ext}"

        await uow.images_writer.create_image_variant(
            image_id=image.id,
            variant="original",
            storage_key=original_key,
            _format=ext,
            width=width,
            height=height,
            byte_size=byte_size,
        )

        # Загружаем в S3 асинхронно
        await _upload_to_s3(
            storage=storage,
            key=original_key,
            data=content,
            content_type=content_type or "application/octet-stream",
        )

        await uow.commit()
        return await get_image(image.id, uow) or image

    except Exception as e:
        await uow.rollback()
        raise ImageProcessingError(f"Не удалось сохранить изображение: {e}") from e


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

    # Удаляем файлы из S3 асинхронно
    for variant in image.variants:
        try:
            await _delete_from_s3(storage, variant.storage_key)
        except Exception as e:
            # Логируем, но не прерываем удаление
            logger.warning(f"Failed to delete S3 object {variant.storage_key}: {e}")

    # Удаляем запись из БД
    await uow.images_writer.delete(image_id)
    await uow.commit()

    return True
