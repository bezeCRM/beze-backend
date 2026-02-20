from __future__ import annotations

from typing import Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.categories.models import Category


class CategoriesRepository:
    @staticmethod
    async def list(session: AsyncSession, *, owner_id: UUID, limit: int, offset: int) -> list[Category]:
        c_owner = cast(ColumnElement[bool], Category.__table__.c.owner_id == owner_id)
        stmt = select(Category).where(c_owner).order_by(Category.__table__.c.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, *, owner_id: UUID, category_id: UUID) -> Optional[Category]:
        c_owner = cast(ColumnElement[bool], Category.__table__.c.owner_id == owner_id)
        c_id = cast(ColumnElement[bool], Category.__table__.c.id == category_id)
        stmt = select(Category).where(c_owner, c_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, *, owner_id: UUID, name: str) -> Category:
        obj = Category(owner_id=owner_id, name=name)
        session.add(obj)
        await session.flush()
        return obj

    @staticmethod
    async def delete(session: AsyncSession, obj: Category) -> None:
        await session.delete(obj)