"""Роутеры для управления отзывами в Admin API."""

from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import admin_uow_dep, require_admin_auth
from leaf_flow.api.v1.admin.schemas.review import (
    ReviewCreate,
    ReviewDetail,
    ReviewUpdate,
)
from leaf_flow.infrastructure.db.admin_uow import AdminUoW


router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


@router.get("", response_model=list[ReviewDetail])
async def list_reviews(
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[ReviewDetail]:
    """Получить список всех отзывов."""
    reviews = await uow.reviews_reader.list_all()
    return [ReviewDetail.model_validate(r, from_attributes=True) for r in reviews]


@router.get("/{review_id}", response_model=ReviewDetail)
async def get_review(
    review_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ReviewDetail:
    """Получить отзыв по ID."""
    review = await uow.reviews_reader.get_by_id(review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")

    return ReviewDetail.model_validate(review, from_attributes=True)


@router.post("", response_model=ReviewDetail, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ReviewDetail:
    """Создать отзыв."""
    review = await uow.reviews_writer.create(
        platform=data.platform,
        author=data.author,
        rating=data.rating,
        text=data.text,
        date=data.date,
    )
    await uow.commit()
    return ReviewDetail.model_validate(review, from_attributes=True)


@router.patch("/{review_id}", response_model=ReviewDetail)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ReviewDetail:
    """Обновить отзыв."""
    if not await uow.reviews_reader.get_by_id(review_id):
        raise HTTPException(status_code=404, detail="Отзыв не найден")

    fields = data.model_dump(exclude_none=True)
    review = await uow.reviews_writer.update(review_id, **fields)
    await uow.commit()
    return ReviewDetail.model_validate(review, from_attributes=True)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> None:
    """Удалить отзыв."""
    if not await uow.reviews_reader.get_by_id(review_id):
        raise HTTPException(status_code=404, detail="Отзыв не найден")

    await uow.reviews_writer.delete(review_id)
    await uow.commit()
