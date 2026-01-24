from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.repositories.users import UserRepository
from leaf_flow.infrastructure.db.repositories.products import ProductRepository
from leaf_flow.infrastructure.db.repositories.categories import CategoryRepository
from leaf_flow.infrastructure.db.repositories.carts import CartWriterRepository, CartReaderRepository
from leaf_flow.infrastructure.db.repositories.orders import OrderRepository, OrderItemRepository
from leaf_flow.infrastructure.db.repositories.tokens import RefreshTokenRepository
from leaf_flow.infrastructure.db.repositories.support_topics import SupportTopicRepository
from leaf_flow.infrastructure.db.repositories.reviews import ExternalReviewRepository
from leaf_flow.infrastructure.db.session import AsyncSessionLocal


@dataclass
class UoW:
    session: AsyncSession
    users: UserRepository
    products: ProductRepository
    categories: CategoryRepository
    carts_writer: CartWriterRepository
    carts_reader: CartReaderRepository
    orders: OrderRepository
    order_items: OrderItemRepository
    refresh_tokens: RefreshTokenRepository
    support_topics: SupportTopicRepository
    external_reviews: ExternalReviewRepository
    async def flush(self): await self.session.flush()
    async def commit(self): await self.session.commit()
    async def rollback(self): await self.session.rollback()


async def get_uow():
    async with AsyncSessionLocal() as s:
        yield UoW(
            session=s,
            users=UserRepository(s),
            products=ProductRepository(s),
            categories=CategoryRepository(s),
            carts_writer=CartWriterRepository(s),
            carts_reader=CartReaderRepository(s),
            orders=OrderRepository(s),
            order_items=OrderItemRepository(s),
            refresh_tokens=RefreshTokenRepository(s),
            support_topics=SupportTopicRepository(s),
            external_reviews=ExternalReviewRepository(s)
        )
