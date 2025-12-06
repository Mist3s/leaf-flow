from decimal import Decimal
from typing import Iterable

from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.domain.entities.cart import CartEntity
from leaf_flow.domain.mappers import map_cart_items_to_entities


def _calc_totals(items: Iterable) -> tuple[int, Decimal]:
    total_count = 0
    total_price = Decimal("0.00")
    for it in items:
        total_count += it.quantity
        total_price += (it.price or Decimal("0.00")) * it.quantity
    return total_count, total_price


async def get_cart(user_id: int, uow: UoW) -> CartEntity:
    cart = await uow.carts.get_or_create_by_user(user_id)
    items = await uow.carts.list_items(cart.id)
    total_count, total_price = _calc_totals(items)
    return CartEntity(
        items=map_cart_items_to_entities(items),
        total_count=total_count,
        total_price=total_price,
    )


async def clear_cart(user_id: int, uow: UoW):
    cart = await uow.carts.get_or_create_by_user(user_id)
    await uow.carts.clear(cart.id)
    await uow.commit()


async def add_item(user_id: int, product_id: str, variant_id: str, quantity: int, uow: UoW) -> CartEntity:
    cart = await uow.carts.get_or_create_by_user(user_id)
    variant = await uow.product_variants.get_for_product(product_id, variant_id)
    if not variant:
        raise ValueError("VARIANT_NOT_FOUND")
    await uow.carts.upsert_item(cart.id, product_id, variant_id, quantity, variant.price)
    await uow.commit()
    return await get_cart(user_id, uow)


async def replace_items(user_id: int, items: list[tuple[str, str, int]], uow: UoW) -> CartEntity:
    cart = await uow.carts.get_or_create_by_user(user_id)
    prepared: list[tuple[str, str, int, Decimal]] = []
    for product_id, variant_id, quantity in items:
        variant = await uow.product_variants.get_for_product(product_id, variant_id)
        if not variant:
            raise ValueError("VARIANT_NOT_FOUND")
        prepared.append((product_id, variant_id, quantity, variant.price))
    await uow.carts.replace_items(cart.id, prepared)
    await uow.commit()
    return await get_cart(user_id, uow)


async def set_quantity(user_id: int, product_id: str, variant_id: str, quantity: int, uow: UoW) -> CartEntity:
    cart = await uow.carts.get_or_create_by_user(user_id)
    if quantity < 0:
        raise ValueError("INVALID_QUANTITY")
    if quantity == 0:
        await uow.carts.remove_item(cart.id, product_id, variant_id)
    else:
        item = await uow.carts.set_quantity(cart.id, product_id, variant_id, quantity)
        if not item:
            raise ValueError("ITEM_NOT_FOUND")
    await uow.commit()
    return await get_cart(user_id, uow)


async def remove_item(user_id: int, product_id: str, variant_id: str, uow: UoW) -> CartEntity:
    cart = await uow.carts.get_or_create_by_user(user_id)
    await uow.carts.remove_item(cart.id, product_id, variant_id)
    await uow.commit()
    return await get_cart(user_id, uow)


