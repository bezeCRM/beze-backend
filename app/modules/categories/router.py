from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.modules.categories.service import CategoryAlreadyExistsError, CategoriesService
from app.modules.users.models import User

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await CategoriesService.list(session, owner_id=current_user.id, limit=limit, offset=offset)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await CategoriesService.create(session, owner_id=current_user.id, name=payload.name)
    except CategoryAlreadyExistsError:
        raise HTTPException(status_code=409, detail="category already exists")


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await CategoriesService.update(
            session,
            owner_id=current_user.id,
            category_id=_to_uuid_or_422(category_id),
            name=payload.name,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="category not found")
    except CategoryAlreadyExistsError:
        raise HTTPException(status_code=409, detail="category already exists")


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await CategoriesService.delete(
            session,
            owner_id=current_user.id,
            category_id=_to_uuid_or_422(category_id),
        )
        return None
    except KeyError:
        raise HTTPException(status_code=404, detail="category not found")


def _to_uuid_or_422(value: str):
    from uuid import UUID

    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid uuid")