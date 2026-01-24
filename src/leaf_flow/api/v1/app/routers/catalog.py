from fastapi import APIRouter, Depends, Query, HTTPException, status, Path

from leaf_flow.api.deps import uow_dep
from leaf_flow.api.v1.app.schemas.catalog import (
    Category, Product, CategoryListResponse,
    ProductListResponse, ProductDetail
)
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import catalog_service


router = APIRouter()


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(uow: UoW = Depends(uow_dep)) -> CategoryListResponse:
    categories = await catalog_service.list_categories(uow)
    return CategoryListResponse(
        items=[
            Category.model_validate(category, from_attributes=True)
            for category in categories
        ]
    )


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    category: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow: UoW = Depends(uow_dep),
) -> ProductListResponse:
    total, items = await catalog_service.list_products(
        uow, category, search, limit, offset
    )
    return ProductListResponse(
        total=total,
        items=[
            Product.model_validate(product, from_attributes=True)
            for product in items
        ],
    )


@router.get(
    "/products/{productId}",
    response_model=ProductDetail,
    responses={404: {"description": "Not found"}},
)
async def get_product(
    product_id: str = Path(..., alias="productId"),
    uow: UoW = Depends(uow_dep)
) -> ProductDetail:
    product = await catalog_service.get_product(uow, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return ProductDetail.model_validate(product, from_attributes=True)
