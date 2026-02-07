"""Роутеры для управления категориями в Admin API."""

from fastapi import APIRouter, Depends, HTTPException, status

from leaf_flow.api.deps import admin_uow_dep, require_admin_auth
from leaf_flow.api.v1.admin.schemas.category import (
    CategoryCreate,
    CategoryDetail,
    CategoryUpdate,
)
from leaf_flow.infrastructure.db.admin_uow import AdminUoW


router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@router.get("", response_model=list[CategoryDetail])
async def list_categories(
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[CategoryDetail]:
    """Получить список всех категорий."""
    categories = await uow.categories_reader.list_all()
    return [CategoryDetail.model_validate(c, from_attributes=True) for c in categories]


@router.get("/{slug}", response_model=CategoryDetail)
async def get_category(
    slug: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> CategoryDetail:
    """Получить категорию по slug."""
    category = await uow.categories_reader.get_by_slug(slug)

    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    return CategoryDetail.model_validate(category, from_attributes=True)


@router.post("", response_model=CategoryDetail, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> CategoryDetail:
    """Создать категорию."""
    category = await uow.categories_writer.create(
        slug=data.slug,
        label=data.label,
        sort_order=data.sort_order,
    )
    await uow.commit()
    return CategoryDetail.model_validate(category, from_attributes=True)


@router.patch("/{slug}", response_model=CategoryDetail)
async def update_category(
    slug: str,
    data: CategoryUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> CategoryDetail:
    """Обновить категорию."""
    fields = data.model_dump(exclude_none=True)
    category = await uow.categories_writer.update(slug, **fields)

    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    await uow.commit()
    return CategoryDetail.model_validate(category, from_attributes=True)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    slug: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> None:
    """Удалить категорию."""
    if not uow.categories_reader.get_by_slug(slug):
        raise HTTPException(status_code=404, detail="Категория не найдена")

    await uow.categories_writer.delete(slug)
    await uow.commit()
