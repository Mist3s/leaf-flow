from dataclasses import dataclass
from typing import Literal


Platform = Literal["yandex", "google", "telegram", "avito"]


@dataclass(slots=True)
class ExternalReviewEntity:
    id: int
    platform: Platform
    author: str
    rating: float
    text: str
    date: str


@dataclass(slots=True)
class ReviewPlatformStatsEntity:
    platform: Platform
    avg_rating: float
    reviews_count: int
