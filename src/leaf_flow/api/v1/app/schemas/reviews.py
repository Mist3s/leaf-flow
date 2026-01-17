from pydantic import BaseModel, ConfigDict
from typing import Literal, List

Platform = Literal["yandex", "google", "telegram", "avito"]

class ExternalReviewsStats(BaseModel):
    platform: Platform
    avg_rating: float
    reviews_count: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExternalReview(BaseModel):
    id: int
    platform: Platform
    author: str
    rating: float
    text: str
    date: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ResponseListExternalReviews(BaseModel):
    reviews: List[ExternalReview]
    platforms: List[ExternalReviewsStats]
    total_count: int
    overall_avg: float



class ResponseStatsExternalReviews(BaseModel):
    platforms: List[ExternalReviewsStats]
    total_count: int
    overall_avg: float
