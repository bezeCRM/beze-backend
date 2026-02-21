from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index
from sqlmodel import Field, SQLModel


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class PlannerTask(SQLModel, table=True):
    __tablename__ = "planner_tasks"
    __table_args__ = (
        Index("ix_planner_tasks_owner_id_created_at", "owner_id", "created_at"),
        Index("ix_planner_tasks_owner_id_date", "owner_id", "date"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False)

    title: str = Field(min_length=1, max_length=256)

    date: dt.date = Field(nullable=False)
    time: dt.time | None = Field(default=None)

    created_at: dt.datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: dt.datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )