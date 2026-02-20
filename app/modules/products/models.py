from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductUnit(str, Enum):
    piece = "piece"
    kg = "kg"


class ProductPhoto(SQLModel, table=True):
    __tablename__ = "product_photos"
    __table_args__ = (Index("ix_product_photos_product_id", "product_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    product_id: UUID = Field(foreign_key="products.id", nullable=False)
    uri: str = Field(min_length=1, max_length=2000)

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


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
    price: int = Field(nullable=False)

    recipe: str | None = Field(default=None, max_length=10000)
    unit: ProductUnit = Field(default=ProductUnit.piece, nullable=False)

    # optional, because in frontend types they are optional
    # store as jsonb for flexibility (list of objects)
    fillings: list[Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    ingredients: list[Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )