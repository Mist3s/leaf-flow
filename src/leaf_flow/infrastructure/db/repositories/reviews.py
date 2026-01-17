from typing import Sequence

from sqlalchemy import select, func, cast, Float
from sqlalchemy.orm import Session

from leaf_flow.infrastructure.db.models.reviews import ExternalReview, PlatformEnum
from leaf_flow.infrastructure.db.repositories.base import Repository

class ExternalReviewRepository(Repository[ExternalReview]):
    def __init__(self, session: Session):
        super().__init__(session, ExternalReview)

    async def get_list(self) -> Sequence[ExternalReview] | None:
        stmt = (
            select(ExternalReview).order_by(ExternalReview.id.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_platform_stats(self) -> Sequence[tuple[PlatformEnum, float, int]]:
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
        return res.all()
