from decimal import Decimal
from typing import Protocol, Optional

from leaf_flow.domain.entities.cart import CartDetailEntity, CartEntity, CartItemEntity


class CartWriter(Protocol):
    async def create_cart(self, user_id: int) -> CartEntity:
        ...

    async def clear(self, cart_id: int) -> None:
        ...

    async def upsert_item(
        self, cart_id: int,
        product_id: str,
        variant_id: str,
        quantity: int,
        price: Decimal
    ) -> CartItemEntity:
        ...

    async def replace_items(
        self,
        cart_id: int,
        items: list[tuple[str, str, int, Decimal]]
    ) -> None:
        ...

    async def set_quantity(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str,
        quantity: int
    ) -> CartItemEntity | None:
        ...

    async def remove_item(
        self,
        cart_id: int,
        product_id: str,
        variant_id: str
    ) -> None:
        ...

    async def delete_by_user_id(self, user_id: int) -> bool:
        ...


class CartReader(Protocol):
    async def get_cart(self, cart_id: int) -> CartDetailEntity:
        ...

    async def get_cart_by_user(self, user_id: int) -> Optional[CartEntity]:
        ...

    async def get_cart_items_by_user(self, user_id: int) -> CartDetailEntity:
        ...
