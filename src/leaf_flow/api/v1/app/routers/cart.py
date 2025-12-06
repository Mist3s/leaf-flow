from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from leaf_flow.api.deps import get_current_user, uow_dep
from leaf_flow.api.v1.app.schemas.cart import Cart as CartSchema, CartItemInput, CartItem
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import cart_service


router = APIRouter()


def _to_cart_schema(
    cart, items, total_count, total_price
) -> CartSchema:
    return CartSchema(
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=(it.price or Decimal("0.00")) * it.quantity,
            )
            for it in items
        ],
        totalCount=total_count,
        totalPrice=total_price,
        updatedAt=cart.updated_at,
    )


@router.get("", response_model=CartSchema)
async def get_cart(
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> CartSchema:
    cart = await cart_service.get_cart(user.id, uow)
    return CartSchema(
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total
            )
            for it in cart.items
        ],
        totalCount=cart.total_count,
        totalPrice=cart.total_price,
        updatedAt=None,
    )


@router.delete("", status_code=204)
async def clear_cart(
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> None:
    await cart_service.clear_cart(user.id, uow)
    return None


@router.post("/items", response_model=CartSchema)
async def add_item(
    payload: CartItemInput,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> CartSchema:
    try:
        cart = await cart_service.add_item(
            user.id, payload.productId, payload.variantId, payload.quantity or 1, uow
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CartSchema(
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total
            )
            for it in cart.items
        ],
        totalCount=cart.total_count,
        totalPrice=cart.total_price,
        updatedAt=None,
    )


class ReplaceCartPayload(BaseModel):
    items: list[CartItemInput]


@router.put("/items", response_model=CartSchema)
async def replace_items(
    payload: ReplaceCartPayload,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> CartSchema:
    try:
        items_tuples = [(it.productId, it.variantId, it.quantity or 1) for it in payload.items]
        cart = await cart_service.replace_items(user.id, items_tuples, uow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CartSchema(
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total
            )
            for it in cart.items
        ],
        totalCount=cart.total_count,
        totalPrice=cart.total_price,
        updatedAt=None,
    )


@router.patch("/items/{product_id}/{variant_id}", response_model=CartSchema)
async def update_quantity(
    product_id: str = Path(...),
    variant_id: str = Path(...),
    payload: dict = None,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> CartSchema:
    quantity = (payload or {}).get("quantity")
    if quantity is None:
        raise HTTPException(status_code=400, detail="quantity is required")
    try:
        cart = await cart_service.set_quantity(user.id, product_id, variant_id, int(quantity), uow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CartSchema(
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total
            )
            for it in cart.items
        ],
        totalCount=cart.total_count,
        totalPrice=cart.total_price,
        updatedAt=None,
    )


@router.delete("/items/{product_id}/{variant_id}", response_model=CartSchema)
async def remove_item(
    product_id: str,
    variant_id: str,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> CartSchema:
    cart = await cart_service.remove_item(user.id, product_id, variant_id, uow)
    return CartSchema(
        items=[
            CartItem(
                productId=it.product_id,
                variantId=it.variant_id,
                quantity=it.quantity,
                price=it.price,
                total=it.total
            )
            for it in cart.items
        ],
        totalCount=cart.total_count,
        totalPrice=cart.total_price,
        updatedAt=None,
    )


