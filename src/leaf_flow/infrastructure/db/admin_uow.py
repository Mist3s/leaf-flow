"""Admin Unit of Work — предоставляет доступ к админским репозиториям."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.admin.attribute import (
    AdminAttributeReader,
    AdminAttributeValueWriter
)
from leaf_flow.application.ports.admin.brew_profile import (
    AdminBrewProfileReader,
    AdminBrewProfileWriter
)
from leaf_flow.application.ports.admin.category import (
    AdminCategoryReader,
    AdminCategoryWriter
)
from leaf_flow.application.ports.admin.order import (
    AdminOrderReader,
    AdminOrderWriter
)
from leaf_flow.application.ports.admin.product import (
    AdminProductReader,
    AdminProductWriter
)
from leaf_flow.application.ports.admin.review import (
    AdminReviewReader,
    AdminReviewWriter
)
from leaf_flow.application.ports.admin.user import (
    AdminUserReader,
    AdminUserWriter
)
from leaf_flow.application.ports.admin.variant import (
    AdminVariantReader,
    AdminVariantWriter,
)
from leaf_flow.application.ports.image import ImageReader, ImageWriter
from leaf_flow.infrastructure.db.repositories.admin import (
    AdminAttributeReaderRepository,
    AdminAttributeValueWriterRepository,
    AdminBrewProfileReaderRepository,
    AdminBrewProfileWriterRepository,
    AdminCategoryReaderRepository,
    AdminCategoryWriterRepository,
    AdminOrderReaderRepository,
    AdminOrderWriterRepository,
    AdminProductReaderRepository,
    AdminProductWriterRepository,
    AdminReviewReaderRepository,
    AdminReviewWriterRepository,
    AdminUserReaderRepository,
    AdminUserWriterRepository,
    AdminVariantReaderRepository,
    AdminVariantWriterRepository
)
from leaf_flow.infrastructure.db.repositories.admin.image import (
    ImageReaderRepository,
    ImageWriterRepository,
)
from leaf_flow.infrastructure.db.session import AsyncSessionLocal


@dataclass
class AdminUoW:
    """Unit of Work для админских операций."""

    session: AsyncSession

    # Images
    images_reader: ImageReader
    images_writer: ImageWriter

    # Products
    products_reader: AdminProductReader
    products_writer: AdminProductWriter

    # Variants
    variants_reader: AdminVariantReader
    variants_writer: AdminVariantWriter

    # Brew Profiles
    brew_profiles_reader: AdminBrewProfileReader
    brew_profiles_writer: AdminBrewProfileWriter

    # Categories
    categories_reader: AdminCategoryReader
    categories_writer: AdminCategoryWriter

    # Orders
    orders_reader: AdminOrderReader
    orders_writer: AdminOrderWriter

    # Reviews
    reviews_reader: AdminReviewReader
    reviews_writer: AdminReviewWriter

    # Users
    users_reader: AdminUserReader
    users_writer: AdminUserWriter

    # Attributes
    attributes_reader: AdminAttributeReader
    attribute_values_writer: AdminAttributeValueWriter

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


async def get_admin_uow():
    """Фабрика AdminUoW для FastAPI Depends.
    
    Автоматически откатывает транзакцию при возникновении исключения.
    """
    async with AsyncSessionLocal() as s:
        uow = AdminUoW(
            session=s,
            # Images
            images_reader=ImageReaderRepository(s),
            images_writer=ImageWriterRepository(s),
            # Products
            products_reader=AdminProductReaderRepository(s),
            products_writer=AdminProductWriterRepository(s),
            # Variants
            variants_reader=AdminVariantReaderRepository(s),
            variants_writer=AdminVariantWriterRepository(s),
            # Brew Profiles
            brew_profiles_reader=AdminBrewProfileReaderRepository(s),
            brew_profiles_writer=AdminBrewProfileWriterRepository(s),
            # Categories
            categories_reader=AdminCategoryReaderRepository(s),
            categories_writer=AdminCategoryWriterRepository(s),
            # Orders
            orders_reader=AdminOrderReaderRepository(s),
            orders_writer=AdminOrderWriterRepository(s),
            # Reviews
            reviews_reader=AdminReviewReaderRepository(s),
            reviews_writer=AdminReviewWriterRepository(s),
            # Users
            users_reader=AdminUserReaderRepository(s),
            users_writer=AdminUserWriterRepository(s),
            # Attributes
            attributes_reader=AdminAttributeReaderRepository(s),
            attribute_values_writer=AdminAttributeValueWriterRepository(s),
        )
        try:
            yield uow
        except Exception:
            await s.rollback()
            raise
