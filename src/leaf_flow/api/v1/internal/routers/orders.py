from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from leaf_flow.api.deps import uow_dep, require_internal_auth, get_celery
from leaf_flow.api.v1.internal.schemas.orders import (
    InternalOrderListResponse, InternalOrderListItem, UpdateOrderStatusRequest,
    InternalOrderDetails, InternalCartItem
)
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.infrastructure.db.models.orders import OrderStatusEnum
from leaf_flow.services import order_service


router = APIRouter()


async def _load_product_and_variant_names(order_items, uow: UoW) -> dict[tuple[str, str], tuple[str, str]]:
    """
    Загружает названия продуктов и веса вариантов для элементов заказа.
    Возвращает словарь: (product_id, variant_id) -> (product_name, variant_weight)
    """
    # Собираем уникальные пары product_id и variant_id
    product_variant_pairs = {(it.product_id, it.variant_id) for it in order_items}
    
    # Загружаем все необходимые продукты одним запросом
    product_ids = list({pid for pid, _ in product_variant_pairs})
    products_map = await uow.products.get_multiple_with_variants(product_ids)
    
    # Формируем результат
    result = {}
    for product_id, variant_id in product_variant_pairs:
        product = products_map.get(product_id)
        if product:
            product_name = product.name
            # Ищем вариант по variant_id
            variant_weight = None
            for variant in product.variants:
                if variant.id == variant_id:
                    variant_weight = variant.weight
                    break
            if variant_weight is not None:
                result[(product_id, variant_id)] = (product_name, variant_weight)
            else:
                # Если вариант не найден, используем пустые значения
                result[(product_id, variant_id)] = (product_name, "")
        else:
            # Если продукт не найден, используем пустые значения
            result[(product_id, variant_id)] = ("", "")
    
    return result


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
    celery: Celery = Depends(get_celery)
) -> InternalOrderDetails:
    """
    Обновляет статус заказа и отправляет уведомление во внешний API.
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
            celery=celery
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
