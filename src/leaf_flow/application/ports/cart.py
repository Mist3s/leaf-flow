from decimal import Decimal
from typing import Protocol, Sequence

from leaf_flow.domain.entities.cart import CartItemEntity, CartEntity


class CartWriter(Protocol):
    async def get_or_create_cart_id(self, user_id: int) -> int:
        ...

    async def clear(self, cart_id: int) -> None:
        ...

    async def add_item(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str,
        qty: int,
        price: Decimal
    ) -> None:
        ...

    async def set_qty(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str,
        qty: int
    ) -> bool:
        ...

    async def remove_item(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str
    ) -> None:
        ...


class CartReader(Protocol):
    async def get_cart(self, user_id: int) -> Sequence[CartItemEntity] | None:
        ...
