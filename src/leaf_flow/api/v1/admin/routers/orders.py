from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from leaf_flow.api.deps import admin_uow_dep, require_admin_auth
from leaf_flow.api.v1.admin.schemas.order import (
    OrderDetail,
    OrderItemsUpdate,
    OrderList,
    OrderStatusUpdate,
    OrderUpdate,
)
from leaf_flow.infrastructure.db.admin_uow import AdminUoW


router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])


@router.get("", response_model=OrderList)
async def list_orders(
    search: str | None = Query(None),
    status: str | None = Query(None),
    user_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep)
) -> OrderList:
    """Получить список заказов с поиском и фильтрацией."""
    total, orders = await uow.orders_reader.list_orders(
        search=search,
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return OrderList(
        total=total,
        items=[OrderDetail.model_validate(o, from_attributes=True) for o in orders],
    )


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep)
) -> OrderDetail:
    """Получить детали заказа."""
    order = await uow.orders_reader.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return OrderDetail.model_validate(order, from_attributes=True)


@router.patch("/{order_id}", response_model=OrderDetail)
async def update_order(
    order_id: str,
    data: OrderUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> OrderDetail:
    """Редактировать заказ."""
    fields = data.model_dump(exclude_none=True)
    order = await uow.orders_writer.update(order_id, **fields)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    await uow.commit()
    return OrderDetail.model_validate(order, from_attributes=True)


@router.patch("/{order_id}/status", response_model=OrderDetail)
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep)
) -> OrderDetail:
    """Изменить статус заказа."""
    if not await uow.orders_reader.get_by_id(order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

    order = await uow.orders_writer.update_status(order_id, data.status)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

    await uow.commit()
    return OrderDetail.model_validate(order, from_attributes=True)


@router.put("/{order_id}/items", response_model=OrderDetail)
async def update_order_items(
    order_id: str,
    data: OrderItemsUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep)
) -> OrderDetail:
    """Изменить состав заказа."""
    if not await uow.orders_reader.get_by_id(order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

    payload = data.model_dump(exclude_none=True)
    items = payload["items"]

    total = Decimal('0')

    for item in items:
        item_total = item.get('price') * item.get('quantity')
        total += item_total

    order = await uow.orders_writer.update_items(order_id, items, total)

    await uow.commit()
    return OrderDetail.model_validate(order, from_attributes=True)
