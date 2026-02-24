from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.profile.models import ProfileSettings


class ProfileSettingsRepository:
    @staticmethod
    async def get_by_owner_id(
        session: AsyncSession,
        *,
        owner_id: UUID,
    ) -> Optional[ProfileSettings]:
        t = ProfileSettings.__table__.c
        stmt = select(ProfileSettings).where(t.owner_id == owner_id)
        res = await session.execute(stmt)
        return res.scalars().one_or_none()