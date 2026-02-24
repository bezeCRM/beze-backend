from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.repository import UsersRepository


class UsersService:
    def __init__(self, repo: UsersRepository) -> None:
        self._repo = repo

    async def register(
        self,
        session: AsyncSession,
        *,
        login: str,
        password: str,
        email: str | None = None,
    ) -> User:
        normalized_login = login.lower().strip()

        existing_login = await self._repo.get_by_login(session, normalized_login)
        if existing_login is not None:
            raise ValueError("login уже существует")

        if email is not None:
            normalized_email = email.lower().strip()
            existing_email = await self._repo.get_by_email(session, normalized_email)
            if existing_email is not None:
                raise ValueError("email уже существует")
        else:
            normalized_email = None

        user = await self._repo.create(
            session,
            login=normalized_login,
            email=normalized_email,
            password_hash=hash_password(password),
        )
        await session.commit()
        await session.refresh(user)
        return user