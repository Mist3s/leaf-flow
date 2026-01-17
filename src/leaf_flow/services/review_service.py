from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.domain.entities.reviews import (
    ReviewPlatformStatsEntity,
    ExternalReviewEntity
)
from leaf_flow.domain.mappers import (
    map_external_review_model_to_entity,
    map_review_stats_model_to_entity
)


async def list_external_reviews(
    uow: UoW
) -> tuple[
    int, float, list[ExternalReviewEntity], list[ReviewPlatformStatsEntity]
]:
    reviews_db = await uow.external_reviews.get_list()
    stats_db = await uow.external_reviews.get_platform_stats()
    reviews = [map_external_review_model_to_entity(review) for review in reviews_db]
    platform_stats = [map_review_stats_model_to_entity(row) for row in stats_db]

    total_count = sum(s.reviews_count for s in platform_stats)
    overall_avg = (
        sum(s.avg_rating * s.reviews_count for s in platform_stats) / total_count
        if total_count > 0 else 0.0
    )

    return total_count, overall_avg, reviews, platform_stats


async def get_external_reviews_stats(
    uow: UoW
) -> tuple[
    int, float, list[ReviewPlatformStatsEntity]
]:
    stats_db = await uow.external_reviews.get_platform_stats()
    platform_stats = [map_review_stats_model_to_entity(row) for row in stats_db]

    total_count = sum(s.reviews_count for s in platform_stats)
    overall_avg = (
        sum(s.avg_rating * s.reviews_count for s in platform_stats) / total_count
        if total_count > 0 else 0.0
    )

    return total_count, overall_avg, platform_stats
