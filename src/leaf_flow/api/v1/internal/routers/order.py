from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from leaf_flow.api.deps import uow_dep, require_internal_auth
from leaf_flow.api.v1.internal.schemas.order import (
    InternalOrderListResponse, InternalOrderListItem, UpdateOrderStatusRequest,
    InternalOrderDetails, InternalCartItem
)
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.infrastructure.db.models.order import OrderStatusEnum
from leaf_flow.services import order_service


router = APIRouter(prefix="/internal/orders", tags=["internal"])


@router.get("", response_model=InternalOrderListResponse)
async def list_user_orders(
    telegram_id: int = Query(...),
    limit: int = Query(5, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> InternalOrderListResponse:
    user = await uow.users_reader.get_by_telegram_id(telegram_id)
    if not user:
        return InternalOrderListResponse(items=[])
    orders = await order_service.list_orders_for_user(user_id=user.id, limit=limit, offset=offset, uow=uow)
    return InternalOrderListResponse(
        items=[
            InternalOrderListItem(
                orderId=o.id,
                customerName=o.customer_name,
                deliveryMethod=o.delivery,
                total=o.total,
                status=o.status,
                createdAt=o.created_at,
            )
            for o in orders
        ]
    )


@router.get("/{order_id}", response_model=InternalOrderDetails)
async def get_order_details(
    order_id: str = Path(...),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> InternalOrderDetails:
    order_tuple = await order_service.get_order(order_id, uow)
    order = order_tuple

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    return InternalOrderDetails(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
        items=[
            InternalCartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
                productName=it.product_name,
                variantWeight=it.variant_weight
            )
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status,
        createdAt=order.created_at
    )


@router.patch("/{order_id}/status", response_model=InternalOrderDetails)
async def update_order_status(
    order_id: str = Path(...),
    payload: UpdateOrderStatusRequest = ...,
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> InternalOrderDetails:
    """
    Обновляет статус заказа и записывает событие в outbox.
    """
    try:
        new_status = OrderStatusEnum(payload.newStatus)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order status: {payload.newStatus}"
        )
    
    try:
        order = await order_service.update_order_status(
            order_id=order_id,
            new_status=new_status,
            comment=payload.comment,
            uow=uow,
        )
    except ValueError as e:
        if str(e) == "ORDER_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return InternalOrderDetails(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
        items=[
            InternalCartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
                productName=it.product_name,
                variantWeight=it.variant_weight
            )
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status,
        createdAt=order.created_at
    )
