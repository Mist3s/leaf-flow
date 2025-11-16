from fastapi import APIRouter, Depends, Query, HTTPException, status

from leaf_flow.api.deps import uow_dep
from leaf_flow.api.v1.app.schemas.catalog import Category, Product, CategoryListResponse, ProductListResponse
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import catalog_service


router = APIRouter()


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(uow: UoW = Depends(uow_dep)) -> CategoryListResponse:
    items = await catalog_service.list_categories(uow)
    return CategoryListResponse(items=[Category(id=i["id"], label=i["label"]) for i in items])


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    category: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow: UoW = Depends(uow_dep),
) -> ProductListResponse:
    total, items = await catalog_service.list_products(uow, category, search, limit, offset)
    return ProductListResponse(
        total=total,
        items=[
            Product(
                id=p.id,
                name=p.name,
                description=p.description,
                category=p.category_slug,
                tags=p.tags,
                image=p.image,
                variants=[v for v in p.variants],
            )
            for p in items
        ],
    )


@router.get("/products/{productId}", response_model=Product, responses={404: {"description": "Not found"}})
async def get_product(productId: str, uow: UoW = Depends(uow_dep)) -> Product:
    product = await catalog_service.get_product(uow, productId)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return Product(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category_slug,
        tags=product.tags,
        image=product.image,
        variants=[v for v in product.variants],
    )


