from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from leaf_flow.api.deps import get_current_user, uow_dep
from leaf_flow.api.v1.app.schemas.orders import (
    OrderRequest, OrderSummary, OrderDetails, OrderListItem, OrderItemDetails
)
from leaf_flow.infrastructure.db.models.orders import DeliveryMethodEnum
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import order_service


router = APIRouter()


async def _load_product_and_variant_names(order_items, uow: UoW) -> dict[tuple[str, str], tuple[str, str]]:
    """
    Загружает названия продуктов и веса вариантов для элементов заказа.
    Возвращает словарь: (product_id, variant_id) -> (product_name, variant_weight)
    """
    product_variant_pairs = {(it.product_id, it.variant_id) for it in order_items}
    product_ids = list({pid for pid, _ in product_variant_pairs})
    products_map = await uow.products.get_multiple_with_variants(product_ids)
    
    result = {}
    for product_id, variant_id in product_variant_pairs:
        product = products_map.get(product_id)
        if product:
            product_name = product.name
            variant_weight = None
            for variant in product.variants:
                if variant.id == variant_id:
                    variant_weight = variant.weight
                    break
            result[(product_id, variant_id)] = (product_name, variant_weight or "")
        else:
            result[(product_id, variant_id)] = ("", "")
    
    return result


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
    orderId: str = Path(...),
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> OrderDetails:
    order_tuple = await order_service.get_order(orderId, uow)
    order = order_tuple[0]
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Загружаем названия продуктов и вариантов
    names_map = await _load_product_and_variant_names(order.items, uow)
    
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
                productName=names_map.get((it.product_id, it.variant_id), ("", ""))[0],
                variantWeight=names_map.get((it.product_id, it.variant_id), ("", ""))[1],
            )
            for it in order.items
        ],
        address=order.address,
        comment=order.comment,
        status=order.status,
        createdAt=order.created_at,
    )


