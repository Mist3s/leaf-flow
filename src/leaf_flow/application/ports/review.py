from typing import Protocol, Sequence

from leaf_flow.domain.entities.reviews import Platform, ExternalReviewEntity


class ExternalReviewReader(Protocol):
    async def get_list(self) -> Sequence[ExternalReviewEntity] | None:
        ...

    async def get_platform_stats(self) -> Sequence[tuple[Platform, float, int]]:
        ...
