import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Request, UploadFile, status
from pydantic import ValidationError

from leaf_flow.api.deps import require_admin_auth, uow_dep
from leaf_flow.api.v1.admin.schemas.products import (
    AdminProductResponse,
    AdminProductVariantResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
)
from leaf_flow.api.v1.app.schemas.catalog import ProductVariant
from leaf_flow.config import settings
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import admin_product_service
from leaf_flow.services.media_service import save_image

router = APIRouter()


def _map_product_entity(product) -> AdminProductResponse:
    return AdminProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category_slug,
        tags=product.tags,
        image=product.image,
        variants=[ProductVariant(id=v.id, weight=v.weight, price=v.price) for v in product.variants],
    )


async def _parse_create_payload(request: Request) -> tuple[ProductCreateRequest, UploadFile | None]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        raw_payload = form.get("payload")
        if raw_payload is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Product payload is required",
            )
        try:
            payload_data = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product payload format",
            ) from exc
        image_upload = form.get("image")
        if image_upload is not None and not isinstance(image_upload, UploadFile):
            image_upload = None
    else:
        try:
            payload_data = await request.json()
        except Exception as exc:  # pragma: no cover - passthrough for FastAPI json parsing
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc
        image_upload = None

    try:
        payload = ProductCreateRequest.model_validate(payload_data)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc

    return payload, image_upload if isinstance(image_upload, UploadFile) else None


@router.post("/", response_model=AdminProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request,
    _: None = Depends(require_admin_auth),
    uow: UoW = Depends(uow_dep),
) -> AdminProductResponse:
    payload, image_upload = await _parse_create_payload(request)

    image_path = payload.image.strip() if payload.image else None
    if image_path is None and image_upload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is required")
    if image_upload:
        try:
            image_path = await save_image(
                image_upload,
                upload_dir=Path(settings.IMAGES_DIR),
                public_prefix=settings.IMAGES_BASE_URL,
            )
        except ValueError as e:
            if str(e) == "UNSUPPORTED_IMAGE_TYPE":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")
            raise

    variant_inputs = [
        admin_product_service.NewProductVariant(**variant.model_dump()) for variant in payload.variants
    ]

    try:
        product = await admin_product_service.create_product(
            product_id=payload.id,
            name=payload.name,
            description=payload.description,
            category_slug=payload.category,
            tags=payload.tags,
            image=image_path or "",
            variants=variant_inputs,
            uow=uow,
        )
    except ValueError as e:
        if str(e) == "CATEGORY_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
        if str(e) == "PRODUCT_EXISTS":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product already exists")
        if str(e) == "VARIANT_EXISTS":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Variant already exists")
        if str(e) == "VARIANT_WEIGHT_CONFLICT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Variant with the same weight already exists",
            )
        raise
    return _map_product_entity(product)


@router.patch(
    "/{productId}",
    response_model=AdminProductResponse,
    responses={404: {"description": "Not found"}},
)
async def update_product(
    payload: ProductUpdateRequest,
    productId: str = PathParam(..., description="Product identifier"),
    _: None = Depends(require_admin_auth),
    uow: UoW = Depends(uow_dep),
) -> AdminProductResponse:
    try:
        product = await admin_product_service.update_product(
            product_id=productId,
            name=payload.name,
            description=payload.description,
            category_slug=payload.category,
            tags=payload.tags,
            image=payload.image,
            uow=uow,
        )
    except ValueError as e:
        if str(e) == "PRODUCT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if str(e) == "CATEGORY_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
        raise
    return _map_product_entity(product)


@router.post(
    "/{productId}/variants",
    response_model=AdminProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Not found"}},
)
async def create_product_variant(
    payload: ProductVariantCreateRequest,
    productId: str = PathParam(..., description="Product identifier"),
    _: None = Depends(require_admin_auth),
    uow: UoW = Depends(uow_dep),
) -> AdminProductVariantResponse:
    try:
        variant = await admin_product_service.add_product_variant(
            product_id=productId,
            variant_id=payload.id,
            weight=payload.weight,
            price=payload.price,
            uow=uow,
        )
    except ValueError as e:
        if str(e) == "PRODUCT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if str(e) == "VARIANT_EXISTS":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Variant already exists")
        if str(e) == "VARIANT_WEIGHT_CONFLICT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Variant with the same weight already exists",
            )
        raise
    return AdminProductVariantResponse(id=variant.id, weight=variant.weight, price=variant.price)


@router.patch(
    "/{productId}/variants/{variantId}",
    response_model=AdminProductVariantResponse,
    responses={404: {"description": "Not found"}},
)
async def update_product_variant(
    payload: ProductVariantUpdateRequest,
    productId: str = PathParam(..., description="Product identifier"),
    variantId: str = PathParam(..., description="Variant identifier"),
    _: None = Depends(require_admin_auth),
    uow: UoW = Depends(uow_dep),
) -> AdminProductVariantResponse:
    try:
        variant = await admin_product_service.update_product_variant(
            product_id=productId,
            variant_id=variantId,
            weight=payload.weight,
            price=payload.price,
            uow=uow,
        )
    except ValueError as e:
        if str(e) == "PRODUCT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if str(e) == "VARIANT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
        if str(e) == "VARIANT_WEIGHT_CONFLICT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Variant with the same weight already exists",
            )
        raise
    return AdminProductVariantResponse(id=variant.id, weight=variant.weight, price=variant.price)
