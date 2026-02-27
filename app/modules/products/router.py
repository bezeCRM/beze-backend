from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.products.repository import ProductsRepository
from app.modules.products.schemas import ProductCreate, ProductRead, ProductUpdate
from app.modules.products.service import (
    CategoryNotFoundError,
    ProductAlreadyExistsError,
    ProductInUseError,
    ProductNotFoundError,
    ProductsService,
)
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["products"])


def _to_product_read(*, product, category, photoes) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        category=category,
        price=product.price,
        fillings=product.fillings,
        ingredients=product.ingredients,
        recipe=product.recipe,
        unit=product.unit,
        photoes=photoes if photoes else None,
        createdAt=product.created_at,
        updatedAt=product.updated_at,
    )


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category_id: UUID | None = Query(default=None),
):
    svc = ProductsService()
    repo = ProductsRepository()

    try:
        products = await svc.list(
            session,
            owner_id=current_user.id,
            limit=limit,
            offset=offset,
            category_id=category_id,
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="category not found")

    product_ids = [p.id for p in products]
    category_ids = {p.category_id for p in products if p.category_id is not None}

    categories_by_id = await repo.get_categories_by_ids(
        session, owner_id=current_user.id, category_ids=category_ids
    )
    photos_by_pid = await repo.get_photos_by_product_ids(session, product_ids=product_ids)

    out: list[ProductRead] = []
    for p in products:
        cat = categories_by_id.get(p.category_id) if p.category_id is not None else None
        out.append(
            _to_product_read(
                product=p,
                category=cat,
                photoes=photos_by_pid.get(p.id, []),
            )
        )
    return out


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = ProductsService()
    repo = ProductsRepository()

    try:
        p = await svc.get_or_404(session, owner_id=current_user.id, product_id=product_id)
    except ProductNotFoundError:
        raise HTTPException(status_code=404, detail="product not found")

    categories_by_id = await repo.get_categories_by_ids(
        session,
        owner_id=current_user.id,
        category_ids={p.category_id} if p.category_id is not None else set(),
    )
    photos_by_pid = await repo.get_photos_by_product_ids(session, product_ids=[p.id])

    cat = categories_by_id.get(p.category_id) if p.category_id is not None else None
    return _to_product_read(
        product=p,
        category=cat,
        photoes=photos_by_pid.get(p.id, []),
    )


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = ProductsService()
    repo = ProductsRepository()

    # important: mode="json" converts uuid to str for jsonb
    fillings = (
        None
        if payload.fillings is None
        else [f.model_dump(mode="json", by_alias=True) for f in payload.fillings]
    )
    ingredients = (
        None
        if payload.ingredients is None
        else [i.model_dump(mode="json", by_alias=True) for i in payload.ingredients]
    )
    photo_uris = payload.photo_uris or []

    try:
        p = await svc.create(
            session,
            owner_id=current_user.id,
            name=payload.name,
            price=payload.price,
            category_id=payload.category_id,
            recipe=payload.recipe,
            unit=payload.unit,
            fillings=fillings,
            ingredients=ingredients,
            photo_uris=photo_uris,
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="category not found")
    except ProductAlreadyExistsError:
        raise HTTPException(status_code=409, detail="product already exists")

    categories_by_id = await repo.get_categories_by_ids(
        session,
        owner_id=current_user.id,
        category_ids={p.category_id} if p.category_id is not None else set(),
    )
    photos_by_pid = await repo.get_photos_by_product_ids(session, product_ids=[p.id])

    cat = categories_by_id.get(p.category_id) if p.category_id is not None else None
    return _to_product_read(
        product=p,
        category=cat,
        photoes=photos_by_pid.get(p.id, []),
    )


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = ProductsService()
    repo = ProductsRepository()

    # important: mode="json" converts uuid to str for jsonb
    fillings = (
        None
        if payload.fillings is None
        else [f.model_dump(mode="json", by_alias=True) for f in payload.fillings]
    )
    ingredients = (
        None
        if payload.ingredients is None
        else [i.model_dump(mode="json", by_alias=True) for i in payload.ingredients]
    )
    photo_uris = payload.photo_uris or []

    try:
        p = await svc.update(
            session,
            owner_id=current_user.id,
            product_id=product_id,
            name=payload.name,
            price=payload.price,
            category_id=payload.category_id,
            recipe=payload.recipe,
            unit=payload.unit,
            fillings=fillings,
            ingredients=ingredients,
            photo_uris=photo_uris,
        )
    except ProductNotFoundError:
        raise HTTPException(status_code=404, detail="product not found")
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="category not found")
    except ProductAlreadyExistsError:
        raise HTTPException(status_code=409, detail="product already exists")

    categories_by_id = await repo.get_categories_by_ids(
        session,
        owner_id=current_user.id,
        category_ids={p.category_id} if p.category_id is not None else set(),
    )
    photos_by_pid = await repo.get_photos_by_product_ids(session, product_ids=[p.id])

    cat = categories_by_id.get(p.category_id) if p.category_id is not None else None
    return _to_product_read(
        product=p,
        category=cat,
        photoes=photos_by_pid.get(p.id, []),
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = ProductsService()
    try:
        await svc.delete(session, owner_id=current_user.id, product_id=product_id)
        return None
    except ProductNotFoundError:
        raise HTTPException(status_code=404, detail="product not found")
    except ProductInUseError:
        raise HTTPException(status_code=409, detail="product is used in orders")