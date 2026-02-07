from typing import Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.admin.review import AdminReviewReader, AdminReviewWriter
from leaf_flow.domain.entities.review import ExternalReviewEntity
from leaf_flow.infrastructure.db.mappers.review import map_external_review_model_to_entity
from leaf_flow.infrastructure.db.models.review import ExternalReview, PlatformEnum
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminReviewReaderRepository(Repository[ExternalReview], AdminReviewReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExternalReview)

    async def get_by_id(self, review_id: int) -> ExternalReviewEntity | None:
        stmt = (
            select(ExternalReview)
            .where(ExternalReview.id == review_id)
        )
        review = (await self.session.execute(stmt)).scalar_one_or_none()

        if not review:
            return None

        return map_external_review_model_to_entity(review)

    async def list_all(self) -> Sequence[ExternalReviewEntity]:
        stmt = select(ExternalReview).order_by(ExternalReview.id.desc())
        result = await self.session.execute(stmt)
        reviews = result.scalars().all()
        return [map_external_review_model_to_entity(r) for r in reviews]


class AdminReviewWriterRepository(Repository[ExternalReview], AdminReviewWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExternalReview)

    async def create(
        self,
        platform: str,
        author: str,
        rating: float,
        text: str,
        date: str,
    ) -> ExternalReviewEntity:
        review = ExternalReview(
            platform=PlatformEnum(platform),
            author=author,
            rating=rating,
            text=text,
            date=date,
        )
        self.session.add(review)
        await self.session.flush()
        return map_external_review_model_to_entity(review)

    async def update(
        self, review_id: int, **fields: object
    ) -> ExternalReviewEntity | None:
        allowed = set(ExternalReview.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(ExternalReview)
            .where(ExternalReview.id == review_id)
            .values(**values)
            .returning(ExternalReview)
        )
        review = (await self.session.execute(stmt)).scalar_one_or_none()
        await self.session.flush()

        if review is None:
            return None

        return map_external_review_model_to_entity(review)

    async def delete(self, review_id: int) -> None:
        stmt = delete(ExternalReview).where(ExternalReview.id == review_id)
        await self.session.execute(stmt)
        await self.session.flush()
