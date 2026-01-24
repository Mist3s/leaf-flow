from typing import Protocol, Sequence

from leaf_flow.domain.entities.cart import CartDetailEntity
from leaf_flow.domain.entities.order import (
    OrderEntity, DeliveryMethod, OrderStatus
)


class OrderReader(Protocol):
    async def get_order_with_items(
        self,
        order_id: str
    ) -> OrderEntity | None:
        ...

    async def list_orders_by_user(
        self,
        user_id: int,
        limit: int,
        offset: int
    ) -> Sequence[OrderEntity]:
        ...


class OrderWriter(Protocol):
    async def create_order_with_items(
        self,
        cart: CartDetailEntity,
        order_id: str,
        user_id: int,
        customer_name: str,
        delivery: DeliveryMethod,
        phone: str,
        address: str | None,
        comment: str | None
    ) -> OrderEntity:
        ...

    async def transfer_orders_to_user(
        self,
        from_user_id: int,
        to_user_id: int
    ) -> int:
        ...

    async def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus
    ) -> OrderEntity:
        ...
