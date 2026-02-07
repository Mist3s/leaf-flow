"""Схемы для отзывов в Admin API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Platform = Literal["yandex", "google", "telegram", "avito"]


class ReviewDetail(BaseModel):
    id: int
    platform: Platform
    author: str
    rating: float
    text: str
    date: str

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    platform: Platform
    author: str = Field(..., min_length=1)
    rating: float = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1)


class ReviewUpdate(BaseModel):
    platform: Platform | None = None
    author: str | None = Field(None, min_length=1, max_length=255)
    rating: float | None = Field(None, ge=1, le=5)
    text: str | None = Field(None, min_length=1, max_length=5000)
    date: str | None = Field(None, min_length=1, max_length=50)


class ReviewList(BaseModel):
    total: int
    items: list[ReviewDetail]
