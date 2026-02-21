from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Order, OrderLine
from app.modules.products.models import Product


class OrdersRepository:
    @staticmethod
    async def list_orders(
        session: AsyncSession,
        *,
        owner_id: UUID,
        limit: int,
        offset: int,
    ) -> list[Order]:
        o = Order.__table__.c
        stmt = (
            select(Order)
            .where(o.owner_id == owner_id)
            .order_by(o.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_order(
        session: AsyncSession,
        *,
        owner_id: UUID,
        order_id: UUID,
    ) -> Optional[Order]:
        o = Order.__table__.c
        stmt = select(Order).where(o.owner_id == owner_id, o.id == order_id)
        res = await session.execute(stmt)
        return res.scalars().one_or_none()

    @staticmethod
    async def get_lines_by_order_ids(
        session: AsyncSession,
        *,
        order_ids: list[UUID],
    ) -> dict[UUID, list[OrderLine]]:
        if not order_ids:
            return {}

        l = OrderLine.__table__.c
        stmt = select(OrderLine).where(l.order_id.in_(order_ids))
        res = await session.execute(stmt)
        items = list(res.scalars().all())

        out: dict[UUID, list[OrderLine]] = {oid: [] for oid in order_ids}
        for line in items:
            out[line.order_id].append(line)
        return out

    @staticmethod
    async def delete_lines_by_order_id(session: AsyncSession, *, order_id: UUID) -> None:
        l = OrderLine.__table__.c
        await session.execute(delete(OrderLine).where(l.order_id == order_id))

    @staticmethod
    async def insert_lines(session: AsyncSession, *, lines: list[OrderLine]) -> None:
        for line in lines:
            session.add(line)

    @staticmethod
    async def get_products_by_ids(
        session: AsyncSession,
        *,
        owner_id: UUID,
        product_ids: set[UUID],
    ) -> dict[UUID, Product]:
        if not product_ids:
            return {}

        p = Product.__table__.c
        stmt = select(Product).where(p.owner_id == owner_id, p.id.in_(product_ids))
        res = await session.execute(stmt)
        items = list(res.scalars().all())
        return {prod.id: prod for prod in items}