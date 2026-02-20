from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.repository import CategoriesRepository
from app.modules.products.models import Product
from app.modules.products.repository import ProductsRepository


class ProductAlreadyExistsError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


class ProductsService:
    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        owner_id: UUID,
        limit: int,
        offset: int,
        category_id: UUID | None,
    ) -> list[Product]:
        if category_id is not None:
            category = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
            if category is None:
                raise CategoryNotFoundError
        return await ProductsRepository.list(
            session,
            owner_id=owner_id,
            limit=limit,
            offset=offset,
            category_id=category_id,
        )

    @staticmethod
    async def get_or_404(session: AsyncSession, *, owner_id: UUID, product_id: UUID) -> Product:
        obj = await ProductsRepository.get(session, owner_id=owner_id, product_id=product_id)
        if obj is None:
            raise KeyError("product not found")
        return obj

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        owner_id: UUID,
        name: str,
        description: str | None,
        price: int,
        category_id: UUID | None,
        is_active: bool,
    ) -> Product:
        if category_id is not None:
            category = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
            if category is None:
                raise CategoryNotFoundError

        try:
            obj = await ProductsRepository.create(
                session,
                owner_id=owner_id,
                name=name,
                description=description,
                price=price,
                category_id=category_id,
                is_active=is_active,
            )
            await session.commit()
            await session.refresh(obj)
            return obj
        except IntegrityError:
            await session.rollback()
            raise ProductAlreadyExistsError

    @staticmethod
    async def update(
        session: AsyncSession,
        *,
        owner_id: UUID,
        product_id: UUID,
        name: str,
        description: str | None,
        price: int,
        category_id: UUID | None,
        is_active: bool,
    ) -> Product:
        obj = await ProductsService.get_or_404(session, owner_id=owner_id, product_id=product_id)

        if category_id is not None:
            category = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
            if category is None:
                raise CategoryNotFoundError

        obj.name = name
        obj.description = description
        obj.price = price
        obj.category_id = category_id
        obj.is_active = is_active
        obj.updated_at = datetime.now(timezone.utc)

        try:
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj
        except IntegrityError:
            await session.rollback()
            raise ProductAlreadyExistsError

    @staticmethod
    async def delete(session: AsyncSession, *, owner_id: UUID, product_id: UUID) -> None:
        obj = await ProductsService.get_or_404(session, owner_id=owner_id, product_id=product_id)
        await ProductsRepository.delete(session, obj)
        await session.commit()