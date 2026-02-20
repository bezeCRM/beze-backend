from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class CategoryRead(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime