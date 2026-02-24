from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    login: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    email: Optional[EmailStr] = None


class UserRead(BaseModel):
    id: UUID
    login: str
    email: Optional[EmailStr]
    created_at: datetime