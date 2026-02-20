from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    price: int = Field(gt=0)
    category_id: UUID | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    price: int = Field(gt=0)
    category_id: UUID | None = None
    is_active: bool


class ProductRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    price: int
    category_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime