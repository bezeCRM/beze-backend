from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Product(SQLModel, table=True):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_products_owner_name"),
        Index("ix_products_owner_id", "owner_id"),
        Index("ix_products_owner_category", "owner_id", "category_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    owner_id: UUID = Field(foreign_key="users.id", nullable=False)
    category_id: UUID | None = Field(default=None, foreign_key="categories.id", nullable=True)

    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)

    price: int = Field(nullable=False)

    is_active: bool = Field(default=True, nullable=False)

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )