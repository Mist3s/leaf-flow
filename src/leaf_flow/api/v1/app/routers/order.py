from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from leaf_flow.api.deps import get_current_user, uow_dep, get_celery
from leaf_flow.api.v1.app.schemas.order import (
    OrderRequest, OrderSummary, OrderDetails, OrderListItem, OrderItemDetails
)
from leaf_flow.infrastructure.db.models.order import DeliveryMethodEnum
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import order_service


router = APIRouter()

@router.post("", response_model=OrderSummary, status_code=201)
async def create_order(
    payload: OrderRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
    celery: Celery = Depends(get_celery)
) -> OrderSummary:
    try:
        delivery = DeliveryMethodEnum(payload.delivery)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid delivery method"
        )
    try:
        order = await order_service.create_order(
            user_id=user.id,
            customer_name=payload.customerName,
            phone=payload.phone,
            delivery=delivery,
            address=payload.address,
            comment=payload.comment,
            expected_total=payload.expectedTotal,
            uow=uow,
            celery=celery
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return OrderSummary(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
    )


@router.get("", response_model=list[OrderListItem])
async def list_orders(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> list[OrderListItem]:
    """Получение списка заказов текущего пользователя."""
    orders = await order_service.list_orders_for_user(user.id, limit, offset, uow)
    return [
        OrderListItem(
            orderId=order.id,
            customerName=order.customer_name,
            deliveryMethod=order.delivery,
            total=order.total,
            status=order.status,
            createdAt=order.created_at,
        )
        for order in orders
    ]


@router.get("/{orderId}", response_model=OrderDetails)
async def get_order(
    order_id: str = Path(..., alias="orderId"),
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> OrderDetails:
    order_tuple = await order_service.get_order(order_id, uow)
    order = order_tuple
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return OrderDetails(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
        items=[
            OrderItemDetails(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
                productName=it.product_name,
                variantWeight=it.variant_weight,
            )
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status,
        createdAt=order.created_at,
    )
