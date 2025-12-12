from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from leaf_flow.api.deps import uow_dep, require_internal_auth
from leaf_flow.api.v1.internal.schemas.orders import InternalOrderListResponse, InternalOrderListItem
from leaf_flow.api.v1.app.schemas.orders import OrderDetails, CartItem
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import order_service


router = APIRouter()


@router.get("", response_model=InternalOrderListResponse)
async def list_user_orders(
    telegram_id: int = Query(...),
    limit: int = Query(5, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> InternalOrderListResponse:
    user = await uow.users.get_by_telegram_id(telegram_id)
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


@router.get("/{order_id}", response_model=OrderDetails)
async def get_order_details(
    order_id: str = Path(...),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> OrderDetails:
    order_tuple = await order_service.get_order(order_id, uow)
    order = order_tuple[0]
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderDetails(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total,
            )
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status,
        createdAt=order.created_at
    )
