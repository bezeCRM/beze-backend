from __future__ import annotations

from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.planner.schemas import PlannerTaskCreate, PlannerTaskRead, PlannerTaskUpdate
from app.modules.planner.service import PlannerTaskNotFoundError, PlannerTasksService
from app.modules.users.models import User

router = APIRouter(prefix="/planner/tasks", tags=["planner"])


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


def _time_to_str(value: time | None) -> str | None:
    if value is None:
        return None
    return value.isoformat(timespec="minutes")


@router.get("", response_model=list[PlannerTaskRead])
async def list_tasks(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    date_from: str = Query(..., alias="from"),
    date_to: str = Query(..., alias="to"),
):
    svc = PlannerTasksService()
    items = await svc.list_in_range(
        session,
        owner_id=current_user.id,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
    )

    out: list[PlannerTaskRead] = []
    for t in items:
        out.append(
            PlannerTaskRead(
                id=t.id,
                title=t.title,
                date=t.date.isoformat(),
                time=_time_to_str(t.time),
                createdAt=t.created_at,
                updatedAt=t.updated_at,
            )
        )
    return out


@router.get("/{task_id}", response_model=PlannerTaskRead)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = PlannerTasksService()
    try:
        t = await svc.get_or_404(session, owner_id=current_user.id, task_id=task_id)
    except PlannerTaskNotFoundError:
        raise HTTPException(status_code=404, detail="planner task not found")

    return PlannerTaskRead(
        id=t.id,
        title=t.title,
        date=t.date.isoformat(),
        time=_time_to_str(t.time),
        createdAt=t.created_at,
        updatedAt=t.updated_at,
    )


@router.post("", response_model=PlannerTaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: PlannerTaskCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = PlannerTasksService()
    try:
        task_time = _parse_time(payload.time) if payload.time else None
        created = await svc.create(
            session,
            owner_id=current_user.id,
            title=payload.title,
            task_date=_parse_date(payload.date),
            task_time=task_time,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PlannerTaskRead(
        id=created.id,
        title=created.title,
        date=created.date.isoformat(),
        time=_time_to_str(created.time),
        createdAt=created.created_at,
        updatedAt=created.updated_at,
    )


@router.put("/{task_id}", response_model=PlannerTaskRead)
async def update_task(
    task_id: UUID,
    payload: PlannerTaskUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = PlannerTasksService()
    try:
        task_time = _parse_time(payload.time) if payload.time else None
        updated = await svc.update(
            session,
            owner_id=current_user.id,
            task_id=task_id,
            title=payload.title,
            task_date=_parse_date(payload.date),
            task_time=task_time,
        )
    except PlannerTaskNotFoundError:
        raise HTTPException(status_code=404, detail="planner task not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PlannerTaskRead(
        id=updated.id,
        title=updated.title,
        date=updated.date.isoformat(),
        time=_time_to_str(updated.time),
        createdAt=updated.created_at,
        updatedAt=updated.updated_at,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = PlannerTasksService()
    try:
        await svc.delete(session, owner_id=current_user.id, task_id=task_id)
        return None
    except PlannerTaskNotFoundError:
        raise HTTPException(status_code=404, detail="planner task not found")