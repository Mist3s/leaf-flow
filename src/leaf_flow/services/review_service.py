from typing import Sequence

from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.domain.entities.reviews import (
    ReviewPlatformStatsEntity,
    ExternalReviewEntity
)


async def list_external_reviews(
    uow: UoW
) -> tuple[int, float, Sequence[ExternalReviewEntity] | None, Sequence[ReviewPlatformStatsEntity]]:
    reviews = await uow.external_reviews_reader.get_list()
    platform_stats = await uow.external_reviews_reader.get_platform_stats()

    total_count = sum(s.reviews_count for s in platform_stats)
    overall_avg = (
        sum(s.avg_rating * s.reviews_count for s in platform_stats) / total_count
        if total_count > 0 else 0.0
    )

    return total_count, overall_avg, reviews, platform_stats


async def get_external_reviews_stats(
    uow: UoW
) -> tuple[int, float, Sequence[ReviewPlatformStatsEntity]]:
    platform_stats = await uow.external_reviews_reader.get_platform_stats()

    total_count = sum(s.reviews_count for s in platform_stats)
    overall_avg = (
        sum(s.avg_rating * s.reviews_count for s in platform_stats) / total_count
        if total_count > 0 else 0.0
    )

    return total_count, overall_avg, platform_stats
