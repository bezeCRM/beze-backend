from __future__ import annotations

from typing import Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.products.models import Product


class ProductsRepository:
    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        owner_id: UUID,
        limit: int,
        offset: int,
        category_id: UUID | None,
    ) -> list[Product]:
        c_owner = cast(ColumnElement[bool], Product.__table__.c.owner_id == owner_id)
        stmt = select(Product).where(c_owner)

        if category_id is not None:
            c_cat = cast(ColumnElement[bool], Product.__table__.c.category_id == category_id)
            stmt = stmt.where(c_cat)

        stmt = stmt.order_by(Product.__table__.c.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get(
        session: AsyncSession,
        *,
        owner_id: UUID,
        product_id: UUID,
    ) -> Optional[Product]:
        c_owner = cast(ColumnElement[bool], Product.__table__.c.owner_id == owner_id)
        c_id = cast(ColumnElement[bool], Product.__table__.c.id == product_id)
        stmt = select(Product).where(c_owner, c_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

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
        obj = Product(
            owner_id=owner_id,
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            is_active=is_active,
        )
        session.add(obj)
        await session.flush()
        return obj

    @staticmethod
    async def delete(session: AsyncSession, obj: Product) -> None:
        await session.delete(obj)