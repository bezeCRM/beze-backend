from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category
from app.modules.categories.repository import CategoriesRepository
from app.modules.products.repository import ProductsRepository


class CategoryAlreadyExistsError(Exception):
    pass


class CategoriesService:
    @staticmethod
    async def list(session: AsyncSession, *, owner_id: UUID, limit: int, offset: int) -> list[Category]:
        return await CategoriesRepository.list(session, owner_id=owner_id, limit=limit, offset=offset)

    @staticmethod
    async def get_or_404(session: AsyncSession, *, owner_id: UUID, category_id: UUID) -> Category:
        obj = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
        if obj is None:
            raise KeyError("category not found")
        return obj

    @staticmethod
    async def create(session: AsyncSession, *, owner_id: UUID, name: str) -> Category:
        try:
            obj = await CategoriesRepository.create(session, owner_id=owner_id, name=name)
            await session.commit()
            await session.refresh(obj)
            return obj
        except IntegrityError:
            await session.rollback()
            raise CategoryAlreadyExistsError

    @staticmethod
    async def update(session: AsyncSession, *, owner_id: UUID, category_id: UUID, name: str) -> Category:
        obj = await CategoriesService.get_or_404(session, owner_id=owner_id, category_id=category_id)
        obj.name = name
        obj.updated_at = datetime.now(timezone.utc)
        try:
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj
        except IntegrityError:
            await session.rollback()
            raise CategoryAlreadyExistsError

    @staticmethod
    async def delete(session: AsyncSession, *, owner_id: UUID, category_id: UUID) -> None:
        obj = await CategoriesService.get_or_404(session, owner_id=owner_id, category_id=category_id)

        try:
            # 1) отвязываем категорию у всех товаров пользователя
            await ProductsRepository.clear_category_for_owner(
                session,
                owner_id=owner_id,
                category_id=category_id,
            )

            # 2) удаляем саму категорию
            await CategoriesRepository.delete(session, obj)

            await session.commit()
        except Exception:
            await session.rollback()
            raise