from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.users.models import User


class UsersRepository:
    @staticmethod
    async def get_by_login(session: AsyncSession, login: str) -> Optional[User]:
        condition = cast(ColumnElement[bool], User.__table__.c.login == login)
        stmt = select(User).where(condition)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

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
    async def create(
        session: AsyncSession,
        *,
        login: str,
        password_hash: str,
        email: str,
    ) -> User:
        user = User(login=login, email=email, password_hash=password_hash)
        session.add(user)
        await session.flush()
        return user

    @staticmethod
    async def update_password(
            session: AsyncSession,
            user: User,
            password_hash: str,
    ) -> None:
        user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc)
        session.add(user)
        await session.flush()