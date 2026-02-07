from typing import Protocol, Sequence

from leaf_flow.domain.entities.review import ExternalReviewEntity


class AdminReviewReader(Protocol):
    async def get_by_id(self, review_id: int) -> ExternalReviewEntity | None: ...

    async def list_all(self) -> Sequence[ExternalReviewEntity]: ...


class AdminReviewWriter(Protocol):
    async def create(
        self,
        platform: str,
        author: str,
        rating: float,
        text: str,
        date: str,
    ) -> ExternalReviewEntity: ...

    async def update(self, review_id: int, **fields: object) -> ExternalReviewEntity | None: ...

    async def delete(self, review_id: int) -> None: ...
