from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.planner.models import PlannerTask


class PlannerTasksRepository:
    @staticmethod
    async def list_tasks_in_range(
        session: AsyncSession,
        *,
        owner_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[PlannerTask]:
        t = PlannerTask.__table__.c
        stmt = (
            select(PlannerTask)
            .where(t.owner_id == owner_id, t.date >= date_from, t.date <= date_to)
            .order_by(t.date.asc(), t.time.asc().nulls_last(), t.created_at.asc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_task(
        session: AsyncSession,
        *,
        owner_id: UUID,
        task_id: UUID,
    ) -> Optional[PlannerTask]:
        t = PlannerTask.__table__.c
        stmt = select(PlannerTask).where(t.owner_id == owner_id, t.id == task_id)
        res = await session.execute(stmt)
        return res.scalars().one_or_none()

    @staticmethod
    async def delete_task(
        session: AsyncSession,
        *,
        owner_id: UUID,
        task_id: UUID,
    ) -> int:
        t = PlannerTask.__table__.c
        stmt = delete(PlannerTask).where(t.owner_id == owner_id, t.id == task_id)
        res = await session.execute(stmt)
        return int(res.rowcount or 0)