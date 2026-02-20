from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.products.schemas import ProductCreate, ProductRead, ProductUpdate
from app.modules.products.service import (
    CategoryNotFoundError,
    ProductAlreadyExistsError,
    ProductsService,
)
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category_id: UUID | None = Query(default=None),
):
    try:
        return await ProductsService.list(
            session,
            owner_id=current_user.id,
            limit=limit,
            offset=offset,
            category_id=category_id,
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="category not found")


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ProductsService.get_or_404(session, owner_id=current_user.id, product_id=product_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="product not found")


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ProductsService.create(
            session,
            owner_id=current_user.id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            category_id=payload.category_id,
            is_active=payload.is_active,
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="category not found")
    except ProductAlreadyExistsError:
        raise HTTPException(status_code=409, detail="product already exists")


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ProductsService.update(
            session,
            owner_id=current_user.id,
            product_id=product_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            category_id=payload.category_id,
            is_active=payload.is_active,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="product not found")
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="category not found")
    except ProductAlreadyExistsError:
        raise HTTPException(status_code=409, detail="product already exists")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await ProductsService.delete(session, owner_id=current_user.id, product_id=product_id)
        return None
    except KeyError:
        raise HTTPException(status_code=404, detail="product not found")