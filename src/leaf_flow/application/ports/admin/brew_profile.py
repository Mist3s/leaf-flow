from typing import Protocol, Sequence

from leaf_flow.domain.entities.product import BrewProfileEntity


class AdminBrewProfileReader(Protocol):
    async def get_by_id(self, profile_id: int) -> BrewProfileEntity | None: ...

    async def list_by_product(self, product_id: str) -> Sequence[BrewProfileEntity]: ...


class AdminBrewProfileWriter(Protocol):
    async def create(
        self,
        product_id: str,
        method: str,
        teaware: str,
        temperature: str,
        brew_time: str,
        weight: str,
        note: str | None,
        sort_order: int,
        is_active: bool
    ) -> BrewProfileEntity: ...

    async def update(
        self,
        profile_id: int,
        **fields: object
    ) -> BrewProfileEntity | None: ...

    async def delete(self, profile_id: int) -> None: ...
