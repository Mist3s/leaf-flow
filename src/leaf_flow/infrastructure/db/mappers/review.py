from sqlalchemy.engine import Row

from leaf_flow.domain.entities.review import ExternalReviewEntity, ReviewPlatformStatsEntity
from leaf_flow.infrastructure.db.models.review import ExternalReview as ExternalReviewModel


def map_external_review_model_to_entity(
    external_review: ExternalReviewModel
) -> ExternalReviewEntity:
    return ExternalReviewEntity(
        id=external_review.id,
        platform=external_review.platform.value,
        author=external_review.author,
        rating=external_review.rating,
        text=external_review.text,
        date=external_review.date
    )


def map_review_stats_model_to_entity(row: Row) -> ReviewPlatformStatsEntity:
    return ReviewPlatformStatsEntity(
        platform=row.platform.value,
        avg_rating=row.avg_rating,
        reviews_count=row.reviews_count
    )
