from typing import Protocol, Sequence

from leaf_flow.domain.entities.category import CategoryEntity


class CategoryReader(Protocol):
    async def get_by_slug(self, slug: str) -> CategoryEntity | None:
        ...

    async def list_categories(self) -> Sequence[CategoryEntity]:
        ...
