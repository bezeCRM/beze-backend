from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category
from app.modules.products.models import Product, ProductPhoto


class ProductsRepository:
    @staticmethod
    async def list_products(
        session: AsyncSession,
        *,
        owner_id: UUID,
        limit: int,
        offset: int,
        category_id: UUID | None,
    ) -> list[Product]:
        p = Product.__table__.c

        stmt = (
            select(Product)
            .where(p.owner_id == owner_id)
            .order_by(p.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if category_id is not None:
            stmt = stmt.where(p.category_id == category_id)

        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_product(
        session: AsyncSession,
        *,
        owner_id: UUID,
        product_id: UUID,
    ) -> Optional[Product]:
        p = Product.__table__.c
        stmt = select(Product).where(p.owner_id == owner_id, p.id == product_id)
        res = await session.execute(stmt)
        return res.scalars().one_or_none()

    @staticmethod
    async def get_categories_by_ids(
        session: AsyncSession,
        *,
        owner_id: UUID,
        category_ids: set[UUID],
    ) -> dict[UUID, Category]:
        if not category_ids:
            return {}

        c = Category.__table__.c
        stmt = select(Category).where(c.owner_id == owner_id, c.id.in_(category_ids))
        res = await session.execute(stmt)
        items = list(res.scalars().all())
        return {cat.id: cat for cat in items}

    @staticmethod
    async def get_photos_by_product_ids(
        session: AsyncSession,
        *,
        product_ids: list[UUID],
    ) -> dict[UUID, list[ProductPhoto]]:
        if not product_ids:
            return {}

        pp = ProductPhoto.__table__.c
        stmt = select(ProductPhoto).where(pp.product_id.in_(product_ids)).order_by(pp.created_at.asc())
        res = await session.execute(stmt)
        items = list(res.scalars().all())

        out: dict[UUID, list[ProductPhoto]] = {pid: [] for pid in product_ids}
        for photo in items:
            out[photo.product_id].append(photo)
        return out

    @staticmethod
    async def replace_photos(
        session: AsyncSession,
        *,
        product_id: UUID,
        photo_uris: list[str],
    ) -> None:
        pp = ProductPhoto.__table__.c
        await session.execute(delete(ProductPhoto).where(pp.product_id == product_id))
        for uri in photo_uris:
            session.add(ProductPhoto(product_id=product_id, uri=uri))

    @staticmethod
    async def clear_category_for_owner(
            session: AsyncSession,
            *,
            owner_id: UUID,
            category_id: UUID,
    ) -> int:
        stmt = (
            update(Product)
            .where(Product.owner_id == owner_id, Product.category_id == category_id)
            .values(category_id=None)
        )
        res = await session.execute(stmt)
        # res.rowcount может быть None в некоторых драйверах, но обычно есть
        return int(res.rowcount or 0)