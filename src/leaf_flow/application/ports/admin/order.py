from decimal import Decimal
from typing import Protocol, Sequence

from leaf_flow.domain.entities.order import OrderEntity


class AdminOrderReader(Protocol):
    async def get_by_id(self, order_id: str) -> OrderEntity | None: ...

    async def list_orders(
        self,
        search: str | None,
        status: str | None,
        user_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[OrderEntity]]: ...


class AdminOrderWriter(Protocol):
    async def update(
        self,
        order_id: str,
        **fields: object
    ) -> OrderEntity | None: ...

    async def update_status(
        self,
        order_id: str,
        status: str
    ) -> OrderEntity: ...

    async def update_items(
        self,
        order_id: str,
        items: list[dict[str, any]],
        total: Decimal
    ) -> OrderEntity: ...

    async def delete_items(
        self,
        order_id: str
    ) -> None: ...
