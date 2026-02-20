from __future__ import annotations

from typing import Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.users.models import User


class UsersRepository:
    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        condition = cast(ColumnElement[bool], User.__table__.c.email == email)
        stmt = select(User).where(condition)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
        condition = cast(ColumnElement[bool], User.__table__.c.id == user_id)
        stmt = select(User).where(condition)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, *, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        session.add(user)
        await session.flush()
        return user

