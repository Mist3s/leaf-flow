from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.repositories.user import UserRepository
from leaf_flow.infrastructure.db.repositories.product import ProductRepository
from leaf_flow.infrastructure.db.repositories.category import CategoryReaderRepository
from leaf_flow.infrastructure.db.repositories.cart import CartWriterRepository, CartReaderRepository
from leaf_flow.infrastructure.db.repositories.order import OrderRepository, OrderItemRepository
from leaf_flow.infrastructure.db.repositories.token import RefreshTokenRepository
from leaf_flow.infrastructure.db.repositories.support_topic import SupportTopicRepository
from leaf_flow.infrastructure.db.repositories.review import ExternalReviewReaderRepository
from leaf_flow.application.ports.product import ProductsReader
from leaf_flow.application.ports.cart import CartWriter, CartReader
from leaf_flow.application.ports.category import CategoryReader
from leaf_flow.application.ports.review import ExternalReviewReader
from leaf_flow.infrastructure.db.session import AsyncSessionLocal


@dataclass
class UoW:
    session: AsyncSession
    users: UserRepository
    products: ProductsReader
    categories_reader: CategoryReader
    carts_writer: CartWriter
    carts_reader: CartReader
    orders: OrderRepository
    order_items: OrderItemRepository
    refresh_tokens: RefreshTokenRepository
    support_topics: SupportTopicRepository
    external_reviews_reader: ExternalReviewReader
    async def flush(self): await self.session.flush()
    async def commit(self): await self.session.commit()
    async def rollback(self): await self.session.rollback()


async def get_uow():
    async with AsyncSessionLocal() as s:
        yield UoW(
            session=s,
            users=UserRepository(s),
            products=ProductRepository(s),
            categories_reader=CategoryReaderRepository(s),
            carts_writer=CartWriterRepository(s),
            carts_reader=CartReaderRepository(s),
            orders=OrderRepository(s),
            order_items=OrderItemRepository(s),
            refresh_tokens=RefreshTokenRepository(s),
            support_topics=SupportTopicRepository(s),
            external_reviews_reader=ExternalReviewReaderRepository(s)
        )
