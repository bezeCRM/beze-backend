from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session as _get_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_session():
        yield session
