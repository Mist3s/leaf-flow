from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.order import OrderWriter, OrderReader
from leaf_flow.infrastructure.db.repositories.user import UserReaderRepository, UserWriterRepository
from leaf_flow.infrastructure.db.repositories.product import ProductRepository
from leaf_flow.infrastructure.db.repositories.category import CategoryReaderRepository
from leaf_flow.infrastructure.db.repositories.cart import CartWriterRepository, CartReaderRepository
from leaf_flow.infrastructure.db.repositories.order import OrderWriterRepository, OrderReaderRepository
from leaf_flow.infrastructure.db.repositories.token import (
    RefreshTokenReaderRepository, RefreshTokenWriterRepository
)
from leaf_flow.infrastructure.db.repositories.support_topic import (
    SupportTopicReaderRepository, SupportTopicWriterRepository
)
from leaf_flow.infrastructure.db.repositories.review import ExternalReviewReaderRepository
from leaf_flow.infrastructure.db.repositories.outbox import (
    OutboxReaderRepository, OutboxWriterRepository
)
from leaf_flow.application.ports.product import ProductsReader
from leaf_flow.application.ports.cart import CartWriter, CartReader
from leaf_flow.application.ports.category import CategoryReader
from leaf_flow.application.ports.review import ExternalReviewReader
from leaf_flow.application.ports.auth import RefreshTokenReader, RefreshTokenWriter
from leaf_flow.application.ports.user import UserReader, UserWriter
from leaf_flow.application.ports.support_topic import SupportTopicReader, SupportTopicWriter
from leaf_flow.application.ports.outbox import OutboxWriter, OutboxReader
from leaf_flow.application.ports.image import ImageReader, ImageWriter
from leaf_flow.infrastructure.db.repositories.admin.image import (
    ImageReaderRepository, ImageWriterRepository
)
from leaf_flow.infrastructure.db.session import AsyncSessionLocal



@dataclass
class UoW:
    session: AsyncSession
    users_reader: UserReader
    users_writer: UserWriter
    products: ProductsReader
    categories_reader: CategoryReader
    carts_writer: CartWriter
    carts_reader: CartReader
    orders_writer: OrderWriter
    orders_reader: OrderReader
    outbox_writer: OutboxWriter
    outbox_reader: OutboxReader
    refresh_tokens_reader: RefreshTokenReader
    refresh_tokens_writer: RefreshTokenWriter
    support_topics_reader: SupportTopicReader
    support_topics_writer: SupportTopicWriter
    external_reviews_reader: ExternalReviewReader
    images_reader: ImageReader
    images_writer: ImageWriter
    async def flush(self): await self.session.flush()
    async def commit(self): await self.session.commit()
    async def rollback(self): await self.session.rollback()


async def get_uow():
    async with AsyncSessionLocal() as s:
        yield UoW(
            session=s,
            users_reader=UserReaderRepository(s),
            users_writer=UserWriterRepository(s),
            products=ProductRepository(s),
            categories_reader=CategoryReaderRepository(s),
            carts_writer=CartWriterRepository(s),
            carts_reader=CartReaderRepository(s),
            orders_writer=OrderWriterRepository(s),
            orders_reader=OrderReaderRepository(s),
            outbox_writer=OutboxWriterRepository(s),
            outbox_reader=OutboxReaderRepository(s),
            refresh_tokens_reader=RefreshTokenReaderRepository(s),
            refresh_tokens_writer=RefreshTokenWriterRepository(s),
            support_topics_reader=SupportTopicReaderRepository(s),
            support_topics_writer=SupportTopicWriterRepository(s),
            external_reviews_reader=ExternalReviewReaderRepository(s),
            images_reader=ImageReaderRepository(s),
            images_writer=ImageWriterRepository(s),
        )
