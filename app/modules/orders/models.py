from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, Numeric
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlmodel import Field, SQLModel

from app.modules.products.models import ProductUnit


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class OrderStatus(str, Enum):
    new = "new"
    inWork = "inWork"
    ready = "ready"
    delivered = "delivered"
    canceled = "canceled"


class OrderDeliveryType(str, Enum):
    pickup = "pickup"
    delivery = "delivery"


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_owner_id_created_at", "owner_id", "created_at"),
        Index("ix_orders_owner_id_date", "owner_id", "date"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False)

    name: str | None = Field(default=None, max_length=256)

    client_name: str = Field(min_length=1, max_length=256)
    client_phone: str | None = Field(default=None, max_length=64)
    order_platform: str | None = Field(default=None, max_length=256)

    delivery_type: OrderDeliveryType = Field(nullable=False)
    address: str | None = Field(default=None, max_length=512)

    date: dt.date = Field(nullable=False)
    time: dt.time = Field(nullable=False)

    notes: str | None = Field(default=None, max_length=10000)

    decor_prices: list[Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    extra: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    references: list[Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    status: OrderStatus = Field(default=OrderStatus.new, nullable=False)
    paid_amount: int = Field(default=0, nullable=False)

    in_planner: bool = Field(default=False, nullable=False)

    total_price: int = Field(default=0, nullable=False)
    last_payment_at: dt.datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    created_at: dt.datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: dt.datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class OrderLine(SQLModel, table=True):
    __tablename__ = "order_lines"
    __table_args__ = (
        Index("ix_order_lines_order_id", "order_id"),
        Index("ix_order_lines_product_id", "product_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id", nullable=False)
    product_id: UUID = Field(foreign_key="products.id", nullable=False)

    amount: float = Field(
        nullable=False,
        sa_type=Numeric(12, 3),
    )  # type: ignore[arg-type]

    filling: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    price: int = Field(nullable=False)

    unit: ProductUnit = Field(
        nullable=False,
        sa_type=ENUM(ProductUnit, name="productunit", create_type=False),
    )  # type: ignore[arg-type]