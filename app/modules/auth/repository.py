from __future__ import annotations

from datetime import datetime
from typing import Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from app.modules.auth.models import RefreshToken


class RefreshTokensRepository:
    @staticmethod
    async def get_active_by_hash(
        session: AsyncSession,
        token_hash: str,
        now: datetime,
    ) -> Optional[RefreshToken]:
        token_hash_col = cast(InstrumentedAttribute[str], RefreshToken.token_hash)
        revoked_at_col = cast(InstrumentedAttribute[datetime | None], RefreshToken.revoked_at)
        expires_at_col = cast(InstrumentedAttribute[datetime], RefreshToken.expires_at)

        cond_token = cast(ColumnElement[bool], token_hash_col == token_hash)
        cond_not_revoked = cast(ColumnElement[bool], revoked_at_col.is_(None))
        cond_not_expired = cast(ColumnElement[bool], expires_at_col > now)

        stmt = select(RefreshToken).where(cond_token, cond_not_revoked, cond_not_expired)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        session.add(rt)
        await session.flush()
        return rt

    @staticmethod
    async def revoke(
        session: AsyncSession,
        token: RefreshToken,
        revoked_at: datetime,
    ) -> None:
        token.revoked_at = revoked_at
        session.add(token)
        await session.flush()
