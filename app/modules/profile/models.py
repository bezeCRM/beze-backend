from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class ProfileSettings(SQLModel, table=True):
    __tablename__ = "profile_settings"
    __table_args__ = (
        UniqueConstraint("owner_id", name="uq_profile_settings_owner_id"),
        Index("ix_profile_settings_owner_id", "owner_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False)

    profile_name: str = Field(min_length=1, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    photo_uri: str | None = Field(default=None, max_length=2048)

    created_at: dt.datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: dt.datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )