"""Роутеры для управления продуктами в Admin API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from leaf_flow.api.deps import admin_uow_dep, require_admin_auth
from leaf_flow.api.v1.admin.schemas.attribute import (
    AttributeDetail,
    AttributeValueDetail,
    ProductAttributeValuesUpdate
)
from leaf_flow.api.v1.admin.schemas.brew_profile import (
    BrewProfileCreate,
    BrewProfileDetail,
    BrewProfileUpdate
)
from leaf_flow.api.v1.admin.schemas.product import (
    ProductCreate,
    ProductDetail,
    ProductList,
    ProductUpdate,
    SuccessResponse,
    SuccessWithAddedResponse,
)
from leaf_flow.api.v1.admin.schemas.variant import (
    VariantCreate,
    VariantDetail,
    VariantUpdate
)
from leaf_flow.infrastructure.db.admin_uow import AdminUoW


router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.get("", response_model=ProductList)
async def list_products(
    search: str | None = Query(None),
    category_slug: str | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ProductList:
    """Получить список продуктов с поиском и фильтрацией."""
    total, products = await uow.products_reader.list_products(
        search=search,
        category_slug=category_slug,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return ProductList(
        total=total,
        items=[ProductDetail.model_validate(p, from_attributes=True) for p in products],
    )


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ProductDetail:
    """Получить детали продукта."""
    product = await uow.products_reader.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return ProductDetail.model_validate(product, from_attributes=True)


@router.post("", response_model=ProductDetail, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ProductDetail:
    """Создать продукт."""
    # Проверяем существование категории
    if not await uow.categories_reader.get_by_slug(data.category_slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Категория '{data.category_slug}' не найдена"
        )

    product = await uow.products_writer.create(
        id=data.id,
        name=data.name,
        description=data.description,
        category_slug=data.category_slug,
        image=data.image,
        product_type_code=data.product_type_code,
        tags=data.tags,
        is_active=data.is_active,
    )
    await uow.commit()
    return ProductDetail.model_validate(product, from_attributes=True)


@router.patch("/{product_id}", response_model=ProductDetail)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> ProductDetail:
    """Обновить продукт."""
    fields = data.model_dump(exclude_none=True)
    product = await uow.products_writer.update(product_id, **fields)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    await uow.commit()
    return ProductDetail.model_validate(product, from_attributes=True)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> None:
    """Удалить продукт."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=404, detail="Продукт не найден")

    await uow.products_writer.delete(product_id)
    await uow.commit()


@router.patch("/{product_id}/active", response_model=SuccessResponse)
async def set_product_active(
    product_id: str,
    is_active: bool = Query(...),
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> SuccessResponse:
    """Изменить активность продукта."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    await uow.products_writer.set_active(product_id, is_active)
    await uow.commit()
    return SuccessResponse()


@router.get("/{product_id}/variants", response_model=list[VariantDetail])
async def list_product_variants(
    product_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[VariantDetail]:
    """Получить варианты продукта."""
    variants = await uow.variants_reader.list_by_product(product_id)
    return [VariantDetail.model_validate(v, from_attributes=True) for v in variants]


@router.post(
    "/{product_id}/variants",
    response_model=VariantDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_variant(
    product_id: str,
    data: VariantCreate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> VariantDetail:
    """Добавить вариант к продукту."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    variant = await uow.variants_writer.create(
        id=data.id,
        product_id=product_id,
        weight=data.weight,
        price=str(data.price),
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    await uow.commit()
    return VariantDetail.model_validate(variant, from_attributes=True)


@router.patch("/{product_id}/variants/{variant_id}", response_model=VariantDetail)
async def update_variant(
    product_id: str,
    variant_id: str,
    data: VariantUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> VariantDetail:
    """Обновить вариант продукта."""
    existing_variant = await uow.variants_reader.get_by_id(variant_id)
    if not existing_variant or existing_variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вариант не найден")

    fields = data.model_dump(exclude_none=True)
    variant = await uow.variants_writer.update(variant_id, **fields)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вариант не найден")
    await uow.commit()
    return VariantDetail.model_validate(variant, from_attributes=True)


@router.delete(
    "/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_variant(
    product_id: str,
    variant_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> None:
    """Удалить вариант продукта."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    variant = await uow.variants_reader.get_by_id(variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вариант не найден")

    await uow.variants_writer.delete(variant_id)
    await uow.commit()


@router.patch("/{product_id}/variants/{variant_id}/active", response_model=SuccessResponse)
async def set_variant_active(
    product_id: str,
    variant_id: str,
    is_active: bool = Query(...),
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> SuccessResponse:
    """Изменить активность варианта."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    variant = await uow.variants_reader.get_by_id(variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вариант не найден")

    await uow.variants_writer.set_active(variant_id, is_active)
    await uow.commit()
    return SuccessResponse()


@router.get("/{product_id}/brew-profiles", response_model=list[BrewProfileDetail])
async def list_brew_profiles(
    product_id: str,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[BrewProfileDetail]:
    """Получить профили заваривания продукта."""
    profiles = await uow.brew_profiles_reader.list_by_product(product_id)
    return [BrewProfileDetail.model_validate(p, from_attributes=True) for p in profiles]


@router.post(
    "/{product_id}/brew-profiles",
    response_model=BrewProfileDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_brew_profile(
    product_id: str,
    data: BrewProfileCreate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> BrewProfileDetail:
    """Добавить профиль заваривания."""
    profile = await uow.brew_profiles_writer.create(
        product_id=product_id,
        method=data.method,
        teaware=data.teaware,
        temperature=data.temperature,
        brew_time=data.brew_time,
        weight=data.weight,
        note=data.note,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    await uow.commit()
    return BrewProfileDetail.model_validate(profile, from_attributes=True)


@router.patch(
    "/{product_id}/brew-profiles/{profile_id}",
    response_model=BrewProfileDetail,
)
async def update_brew_profile(
    product_id: str,
    profile_id: int,
    data: BrewProfileUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> BrewProfileDetail:
    """Обновить профиль заваривания."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    if not await uow.brew_profiles_reader.get_by_id(profile_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден")

    fields = data.model_dump(exclude_none=True)

    profile = await uow.brew_profiles_writer.update(profile_id, **fields)
    await uow.commit()

    return BrewProfileDetail.model_validate(profile, from_attributes=True)


@router.delete(
    "/{product_id}/brew-profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_brew_profile(
    product_id: str,
    profile_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> None:
    """Удалить профиль заваривания."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    if not await uow.brew_profiles_reader.get_by_id(profile_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден")

    await uow.brew_profiles_writer.delete(profile_id)
    await uow.commit()


@router.put("/{product_id}/attributes", response_model=SuccessResponse)
async def set_product_attribute_values(
    product_id: str,
    data: ProductAttributeValuesUpdate,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> SuccessResponse:
    """Установить значения атрибутов для продукта."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    await uow.attribute_values_writer.set_product_values(
        product_id=product_id,
        attribute_value_ids=data.attribute_value_ids,
    )
    await uow.commit()
    return SuccessResponse()


@router.post("/{product_id}/attributes/{attribute_value_id}", response_model=SuccessWithAddedResponse)
async def add_attribute_value_to_product(
    product_id: str,
    attribute_value_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> SuccessWithAddedResponse:
    """Добавить значение атрибута к продукту."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    added = await uow.attribute_values_writer.add_to_product(
        product_id=product_id,
        attribute_value_id=attribute_value_id,
    )
    await uow.commit()
    return SuccessWithAddedResponse(added=added)


@router.delete(
    "/{product_id}/attributes/{attribute_value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_attribute_value_from_product(
    product_id: str,
    attribute_value_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> None:
    """Удалить значение атрибута у продукта."""
    if not await uow.products_reader.get_by_id(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    await uow.attribute_values_writer.remove_from_product(
        product_id=product_id,
        attribute_value_id=attribute_value_id,
    )
    await uow.commit()


@router.get("/attributes/list", response_model=list[AttributeDetail])
async def list_attributes(
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[AttributeDetail]:
    """Получить список всех атрибутов с их значениями."""
    attrs = await uow.attributes_reader.list_all()
    return [AttributeDetail.model_validate(a, from_attributes=True) for a in attrs]


@router.get("/attributes/{attribute_id}", response_model=AttributeDetail)
async def get_attribute(
    attribute_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> AttributeDetail:
    """Получить атрибут по ID."""
    attr = await uow.attributes_reader.get_by_id(attribute_id)

    if not attr:
        raise HTTPException(status_code=404, detail="Атрибут не найден")

    return AttributeDetail.model_validate(attr, from_attributes=True)


@router.get(
    "/attributes/{attribute_id}/values",
    response_model=list[AttributeValueDetail],
)
async def list_attribute_values(
    attribute_id: int,
    _: None = Depends(require_admin_auth),
    uow: AdminUoW = Depends(admin_uow_dep),
) -> list[AttributeValueDetail]:
    """Получить значения атрибута."""
    if not await uow.attributes_reader.get_by_id(attribute_id):
        raise HTTPException(status_code=404, detail="Атрибут не найден")

    values = await uow.attributes_reader.get_values_by_attribute(attribute_id)
    return [AttributeValueDetail.model_validate(v, from_attributes=True) for v in values]
