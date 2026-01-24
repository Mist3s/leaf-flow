from typing import Sequence

from sqlalchemy import select, func, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.review import ExternalReviewReader
from leaf_flow.infrastructure.db.mappers.review import (
    map_external_review_model_to_entity,
    map_review_stats_model_to_entity
)
from leaf_flow.infrastructure.db.models.reviews import ExternalReview
from leaf_flow.infrastructure.db.repositories.base import Repository
from leaf_flow.domain.entities.reviews import (
    ExternalReviewEntity,
    ReviewPlatformStatsEntity
)


class ExternalReviewReaderRepository(Repository[ExternalReview], ExternalReviewReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExternalReview)

    async def get_list(self) -> Sequence[ExternalReviewEntity] | None:
        stmt = (
            select(ExternalReview).order_by(ExternalReview.id.desc())
        )
        res = await self.session.execute(stmt)
        return [map_external_review_model_to_entity(review) for review in res.scalars().all()]

    async def get_platform_stats(self) -> Sequence[ReviewPlatformStatsEntity]:
        stmt = (
            select(
                ExternalReview.platform.label("platform"),
                cast(func.avg(ExternalReview.rating), Float).label("avg_rating"),
                func.count(ExternalReview.id).label("reviews_count"),
            )
            .group_by(ExternalReview.platform)
            .order_by(ExternalReview.platform)
        )

        res = await self.session.execute(stmt)
        return [map_review_stats_model_to_entity(row) for row in res]
