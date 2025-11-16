from fastapi import APIRouter, Depends, HTTPException, Path, status

from leaf_flow.api.deps import get_current_user, uow_dep
from leaf_flow.api.v1.app.schemas.orders import OrderRequest, OrderSummary, OrderDetails
from leaf_flow.infrastructure.db.models.orders import DeliveryMethodEnum
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import order_service


router = APIRouter()


@router.post("", response_model=OrderSummary, status_code=201)
async def create_order(
    payload: OrderRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> OrderSummary:
    try:
        delivery = DeliveryMethodEnum(payload.delivery)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid delivery method")
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
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return OrderSummary(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
    )


@router.get("/{orderId}", response_model=OrderDetails)
async def get_order(
    orderId: str = Path(...),
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> OrderDetails:
    order_tuple = await order_service.get_order(orderId, uow)
    order = order_tuple[0]
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderDetails(
        orderId=order.id,
        customerName=order.customer_name,
        deliveryMethod=order.delivery,
        total=order.total,
        items=[
            {
                "productId": it.product_id,
                "variantId": it.variant_id,
                "quantity": it.quantity,
                "price": it.price,
                "total": it.total,
            }
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status,
        createdAt=order.created_at,
    )


