from typing import Protocol, Sequence

from leaf_flow.domain.entities.category import CategoryEntity


class AdminCategoryReader(Protocol):
    async def get_by_slug(self, slug: str) -> CategoryEntity | None: ...

    async def list_all(self) -> Sequence[CategoryEntity]: ...


class AdminCategoryWriter(Protocol):
    async def create(
        self,
        slug: str,
        label: str,
        sort_order: int,
    ) -> CategoryEntity: ...

    async def update(self, slug: str, **fields: object) -> CategoryEntity | None: ...

    async def delete(self, slug: str) -> None: ...
