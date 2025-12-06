from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.infrastructure.db.repositories.users import UserRepository
from leaf_flow.infrastructure.db.repositories.products import ProductRepository, ProductVariantRepository
from leaf_flow.infrastructure.db.repositories.categories import CategoryRepository
from leaf_flow.infrastructure.db.repositories.carts import CartRepository
from leaf_flow.infrastructure.db.repositories.orders import OrderRepository, OrderItemRepository
from leaf_flow.infrastructure.db.repositories.tokens import RefreshTokenRepository
from leaf_flow.infrastructure.db.session import AsyncSessionLocal


@dataclass
class UoW:
    session: AsyncSession
    users: UserRepository
    products: ProductRepository
    product_variants: ProductVariantRepository
    categories: CategoryRepository
    carts: CartRepository
    orders: OrderRepository
    order_items: OrderItemRepository
    refresh_tokens: RefreshTokenRepository
    async def flush(self): await self.session.flush()
    async def commit(self): await self.session.commit()
    async def rollback(self): await self.session.rollback()


async def get_uow():
    async with AsyncSessionLocal() as s:
        yield UoW(
            session=s,
            users=UserRepository(s),
            products=ProductRepository(s),
            product_variants=ProductVariantRepository(s),
            categories=CategoryRepository(s),
            carts=CartRepository(s),
            orders=OrderRepository(s),
            order_items=OrderItemRepository(s),
            refresh_tokens=RefreshTokenRepository(s),
        )
