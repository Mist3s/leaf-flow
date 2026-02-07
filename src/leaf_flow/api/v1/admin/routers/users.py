"""Роутеры для управления пользователями в Admin API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from leaf_flow.api.deps import admin_uow_dep, require_admin_auth
from leaf_flow.api.v1.admin.schemas.user import (
    UserDetail,
    UserList,
    UserUpdate,
)
from leaf_flow.infrastructure.db.admin_uow import AdminUoW


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=UserList)
async def list_users(
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> UserList:
    """Получить список пользователей с поиском."""
    total, users = await uow.users_reader.list_users(
        search=search,
        limit=limit,
        offset=offset,
    )
    return UserList(
        total=total,
        items=[UserDetail.model_validate(u, from_attributes=True) for u in users],
    )


@router.get("/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> UserDetail:
    """Получить пользователя по ID."""
    user = await uow.users_reader.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserDetail.model_validate(user, from_attributes=True)


@router.patch("/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: int,
    data: UserUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> UserDetail:
    """Редактировать пользователя."""
    fields = data.model_dump(exclude_none=True)
    user = await uow.users_writer.update(user_id, **fields)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    await uow.commit()
    return UserDetail.model_validate(user, from_attributes=True)
