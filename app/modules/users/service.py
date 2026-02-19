from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.repository import UsersRepository
from app.modules.users.models import User


class UsersService:
    def __init__(self, repo: UsersRepository) -> None:
        self._repo = repo

    async def register(self, session: AsyncSession, *, email: str, password: str) -> User:
        existing = await self._repo.get_by_email(session, email)
        if existing is not None:
            raise ValueError("email already exists")

        user = await self._repo.create(session, email=email, password_hash=hash_password(password))
        await session.commit()
        await session.refresh(user)
        return user
