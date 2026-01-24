from decimal import Decimal
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.cart import CartWriter, CartReader
from leaf_flow.infrastructure.db.models.carts import Cart, CartItem
from leaf_flow.infrastructure.db.repositories.base import Repository
from leaf_flow.domain.entities.cart import (
    CartDetailEntity,
    CartEntity,
    CartItemEntity
)
from leaf_flow.infrastructure.db.mappers.cart import (
    map_cart_detail_to_entities,
    map_cart_to_entities,
    map_cart_item_to_entities
)


class CartReaderRepository(Repository[Cart], CartReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Cart)

    async def get_cart(self, cart_id: int) -> CartDetailEntity:
        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .options(
                selectinload(CartItem.product),
                selectinload(CartItem.variant),
            )
            .order_by(CartItem.id)
        )
        cart = await self.session.execute(stmt)
        return map_cart_detail_to_entities(cart.scalars().all())

    async def get_cart_by_user(self, user_id: int) -> Optional[CartEntity]:
        stmt = select(Cart).where(Cart.user_id == user_id)
        cart = (await self.session.scalars(stmt)).one_or_none()
        return map_cart_to_entities(cart) if cart is not None else None

    async def get_cart_items_by_user(self, user_id: int) -> CartDetailEntity:
        stmt = (
            select(CartItem)
            .join(CartItem.cart)
            .where(Cart.user_id == user_id)
            .options(
                selectinload(CartItem.product),
                selectinload(CartItem.variant)
            )
            .order_by(CartItem.id)
        )
        cart = await self.session.execute(stmt)
        return map_cart_detail_to_entities(cart.scalars().all())


class CartWriterRepository(Repository[Cart], CartWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Cart)

    async def create_cart(self, user_id: int) -> CartEntity:
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return map_cart_to_entities(cart)

    async def clear(self, cart_id: int) -> None:
        await self.session.execute(
            delete(
                CartItem
            ).where(
                CartItem.cart_id == cart_id
            )
        )

    async def upsert_item(
        self, cart_id: int,
        product_id: str,
        variant_id: str,
        quantity: int,
        price: Decimal
    ) -> CartItemEntity:
        stmt = (
            select(CartItem)
            .where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
                CartItem.variant_id == variant_id,
            )
            .options(
                selectinload(CartItem.product),
                selectinload(CartItem.variant)
            )
            .order_by(CartItem.id)
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()

        if item:
            item.quantity = item.quantity + quantity
            await self.session.flush()
            return map_cart_item_to_entities(item)

        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            price=price
        )
        self.session.add(item)
        await self.session.flush()

        item = (
            await self.session.scalars(
                select(CartItem)
                .where(CartItem.id == item.id)
                .options(
                    selectinload(CartItem.product),
                    selectinload(CartItem.variant)
                )
            )
        ).one()

        return map_cart_item_to_entities(item)

    async def replace_items(
        self,
        cart_id: int,
        items: list[tuple[str, str, int, Decimal]]
    ) -> None:
        await self.clear(cart_id)
        for product_id, variant_id, quantity, price in items:
            self.session.add(
                CartItem(
                    cart_id=cart_id,
                    product_id=product_id,
                    variant_id=variant_id,
                    quantity=quantity,
                    price=price
                )
            )
        await self.session.flush()

    async def set_quantity(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str,
        quantity: int
    ) -> CartItemEntity | None:
        stmt = (
            select(CartItem)
            .where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
                CartItem.variant_id == variant_id
            )
            .options(
                selectinload(CartItem.product),
                selectinload(CartItem.variant)
            )
            .order_by(CartItem.id)
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()

        if not item:
            return None

        item.quantity = quantity
        await self.session.flush()
        return map_cart_item_to_entities(item)

    async def remove_item(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str
    ) -> None:
        await self.session.execute(
            delete(CartItem)
            .where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
                CartItem.variant_id == variant_id,
            )
        )

    async def delete_by_user_id(self, user_id: int) -> bool:
        """
        Удаляет корзину пользователя (вместе с товарами через CASCADE).
        
        Returns:
            True если корзина была удалена, False если её не существовало
        """
        stmt = select(Cart).where(Cart.user_id == user_id)
        result = await self.session.execute(stmt)
        cart = result.scalar_one_or_none()

        if cart:
            await self.session.delete(cart)
            return True

        return False
