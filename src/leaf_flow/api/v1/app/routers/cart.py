from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from leaf_flow.api.deps import get_current_user, uow_dep
from leaf_flow.api.v1.app.schemas.cart import CartSchema, CartItemInput, UpdateQuantityRequest
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import cart_service


router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartSchema)
async def get_cart(
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> CartSchema:
    cart = await cart_service.get_cart(user.id, uow)
    return CartSchema.model_validate(cart, from_attributes=True)


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
            user.id,
            payload.productId,
            payload.variantId,
            payload.quantity or 1,
            uow
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CartSchema.model_validate(cart, from_attributes=True)


class ReplaceCartPayload(BaseModel):
    items: list[CartItemInput]


@router.put("/items", response_model=CartSchema)
async def replace_items(
    payload: ReplaceCartPayload,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep)
) -> CartSchema:
    try:
        items_tuples = [
            (
                it.productId,
                it.variantId,
                it.quantity or 1
            ) for it in payload.items
        ]
        cart = await cart_service.replace_items(
            user.id, items_tuples, uow
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CartSchema.model_validate(cart, from_attributes=True)


@router.patch("/items/{product_id}/{variant_id}", response_model=CartSchema)
async def update_quantity(
    product_id: str,
    variant_id: str,
    payload: UpdateQuantityRequest,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> CartSchema:
    try:
        cart = await cart_service.set_quantity(
            user.id, product_id, variant_id, payload.quantity, uow
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CartSchema.model_validate(cart, from_attributes=True)


@router.delete("/items/{product_id}/{variant_id}", response_model=CartSchema)
async def remove_item(
    product_id: str,
    variant_id: str,
    user: UserEntity = Depends(get_current_user),
    uow: UoW = Depends(uow_dep),
) -> CartSchema:
    cart = await cart_service.remove_item(user.id, product_id, variant_id, uow)
    return CartSchema.model_validate(cart, from_attributes=True)
