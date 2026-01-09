from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.carts import Cart, CartItem
from leaf_flow.infrastructure.db.repositories.base import Repository


class CartRepository(Repository[Cart]):
    def __init__(self, session: Session):
        super().__init__(session, Cart)

    async def get_or_create_by_user(self, user_id: int) -> Cart:
        stmt = select(Cart).where(Cart.user_id == user_id)
        result = await self.session.execute(stmt)
        cart = result.scalar_one_or_none()
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def clear(self, cart_id: int) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))

    async def list_items(self, cart_id: int) -> Sequence[CartItem]:
        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .order_by(CartItem.id)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def upsert_item(self, cart_id: int, product_id: str, variant_id: str, quantity: int, price: Decimal) -> CartItem:
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
            CartItem.variant_id == variant_id,
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()
        if item:
            item.quantity = item.quantity + quantity
            await self.session.flush()
            return item
        item = CartItem(cart_id=cart_id, product_id=product_id, variant_id=variant_id, quantity=quantity, price=price)
        self.session.add(item)
        await self.session.flush()
        return item

    async def replace_items(self, cart_id: int, items: list[tuple[str, str, int, Decimal]]) -> None:
        await self.clear(cart_id)
        for product_id, variant_id, quantity, price in items:
            self.session.add(
                CartItem(cart_id=cart_id, product_id=product_id, variant_id=variant_id, quantity=quantity, price=price)
            )
        await self.session.flush()

    async def set_quantity(self, cart_id: int, product_id: str, variant_id: str, quantity: int) -> CartItem | None:
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
            CartItem.variant_id == variant_id,
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()
        if not item:
            return None
        item.quantity = quantity
        await self.session.flush()
        return item

    async def remove_item(self, cart_id: int, product_id: str, variant_id: str) -> None:
        await self.session.execute(
            delete(CartItem).where(
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


