from fastapi import APIRouter, Depends

from leaf_flow.api.deps import uow_dep
from leaf_flow.api.v1.app.schemas.reviews import (
    ExternalReviewsStats,
    ExternalReview,
    ResponseStatsExternalReviews,
    ResponseListExternalReviews
)

from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import review_service

router = APIRouter()

@router.get("/external/stats", response_model=ResponseStatsExternalReviews)
async def get_external_reviews_stats(uow: UoW = Depends(uow_dep)) -> ResponseStatsExternalReviews:
    total_count, overall_avg, platform_stats = await review_service.get_external_reviews_stats(uow)
    return ResponseStatsExternalReviews(
        platforms = [
            ExternalReviewsStats.model_validate(
                stats, from_attributes=True
            ) for stats in platform_stats
        ],
        total_count = total_count,
        overall_avg = overall_avg
    )


@router.get("/external", response_model=ResponseListExternalReviews)
async def list_external_reviews(uow: UoW = Depends(uow_dep)) -> ResponseListExternalReviews:
    total_count, overall_avg, reviews, platform_stats = await review_service.list_external_reviews(uow)
    return ResponseListExternalReviews(
        reviews = [
            ExternalReview.model_validate(
                review, from_attributes=True
            ) for review in reviews
        ],
        platforms=[
            ExternalReviewsStats.model_validate(
                stats, from_attributes=True
            ) for stats in platform_stats
        ],
        total_count = total_count,
        overall_avg = overall_avg
    )
