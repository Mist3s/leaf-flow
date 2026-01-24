from decimal import Decimal

from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.domain.entities.cart import CartDetailEntity, CartEntity


async def _get_or_create_cart(user_id: int, uow: UoW) -> CartEntity:
    cart = await uow.carts_reader.get_cart_by_user(user_id)

    if cart is None:
        cart = await uow.carts_writer.create_cart(user_id)

    return cart


async def get_cart(user_id: int, uow: UoW) -> CartDetailEntity:
    cart = await uow.carts_reader.get_cart_by_user(user_id)

    if not cart:
        cart = await uow.carts_writer.create_cart(user_id)
        await uow.commit()

    return await uow.carts_reader.get_cart(cart.id)


async def clear_cart(user_id: int, uow: UoW):
    cart = await _get_or_create_cart(user_id, uow)
    await uow.carts_writer.clear(cart.id)
    await uow.commit()


async def add_item(
    user_id: int,
    product_id: str,
    variant_id: str,
    quantity: int,
    uow: UoW
) -> CartDetailEntity:
    cart = await _get_or_create_cart(user_id, uow)
    variant = await uow.products.get_for_product_variant(product_id, variant_id)

    if not variant:
        raise ValueError("VARIANT_NOT_FOUND")

    await uow.carts_writer.upsert_item(
        cart.id,
        product_id,
        variant_id,
        quantity,
        variant.price
    )
    await uow.commit()
    return await uow.carts_reader.get_cart(cart.id)


async def replace_items(
    user_id: int,
    items: list[tuple[str, str, int]],
    uow: UoW
) -> CartDetailEntity:
    cart = await _get_or_create_cart(user_id, uow)
    keys = [
        (product_id, variant_id)
        for product_id, variant_id, _ in items
    ]
    variants_map = await uow.products.get_for_product_variants(keys)
    
    prepared: list[tuple[str, str, int, Decimal]] = []
    for product_id, variant_id, quantity in items:
        variant = variants_map.get((product_id, variant_id))

        if not variant:
            raise ValueError("VARIANT_NOT_FOUND")

        prepared.append(
            (
                product_id,
                variant_id,
                quantity,
                variant.price
            )
        )

    await uow.carts_writer.replace_items(cart.id, prepared)
    await uow.commit()
    return await uow.carts_reader.get_cart(cart.id)


async def set_quantity(
    user_id: int,
    product_id: str,
    variant_id: str,
    quantity: int,
    uow: UoW
) -> CartDetailEntity:
    cart = await _get_or_create_cart(user_id, uow)

    if quantity < 0:
        raise ValueError("INVALID_QUANTITY")

    if quantity == 0:
        await uow.carts_writer.remove_item(
            cart.id, product_id, variant_id
        )

    else:
        item = await uow.carts_writer.set_quantity(
            cart.id, product_id, variant_id, quantity
        )

        if not item:
            raise ValueError("ITEM_NOT_FOUND")

    await uow.commit()
    return await uow.carts_reader.get_cart(cart.id)


async def remove_item(
    user_id: int,
    product_id: str,
    variant_id: str,
    uow: UoW
) -> CartDetailEntity:
    cart = await uow.carts_reader.get_cart_by_user(user_id)

    if not cart:
        cart = await uow.carts_writer.create_cart(user_id)
        await uow.commit()
        return await uow.carts_reader.get_cart(cart.id)

    await uow.carts_writer.remove_item(
        cart.id, product_id, variant_id
    )
    await uow.commit()
    return await uow.carts_reader.get_cart(cart.id)
