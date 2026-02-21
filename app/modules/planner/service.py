from __future__ import annotations

from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.planner.models import PlannerTask
from app.modules.planner.repository import PlannerTasksRepository


class PlannerTaskNotFoundError(Exception):
    pass


class PlannerTasksService:
    def __init__(self) -> None:
        self._repo = PlannerTasksRepository()

    async def list_in_range(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[PlannerTask]:
        return await self._repo.list_tasks_in_range(
            session,
            owner_id=owner_id,
            date_from=date_from,
            date_to=date_to,
        )

    async def get_or_404(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        task_id: UUID,
    ) -> PlannerTask:
        obj = await self._repo.get_task(session, owner_id=owner_id, task_id=task_id)
        if obj is None:
            raise PlannerTaskNotFoundError
        return obj

    async def create(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        title: str,
        task_date: date,
        task_time: time | None,
    ) -> PlannerTask:
        obj = PlannerTask(
            owner_id=owner_id,
            title=title,
            date=task_date,
            time=task_time,
        )
        session.add(obj)
        await session.commit()
        return await self.get_or_404(session, owner_id=owner_id, task_id=obj.id)

    async def update(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        task_id: UUID,
        title: str,
        task_date: date,
        task_time: time | None,
    ) -> PlannerTask:
        obj = await self.get_or_404(session, owner_id=owner_id, task_id=task_id)

        obj.title = title
        obj.date = task_date
        obj.time = task_time
        obj.updated_at = datetime.now(timezone.utc)

        session.add(obj)
        await session.commit()
        return await self.get_or_404(session, owner_id=owner_id, task_id=task_id)

    async def delete(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        task_id: UUID,
    ) -> None:
        obj = await self.get_or_404(session, owner_id=owner_id, task_id=task_id)
        await session.delete(obj)
        await session.commit()