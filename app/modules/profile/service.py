from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.profile.models import ProfileSettings
from app.modules.profile.repository import ProfileSettingsRepository


class ProfileSettingsService:
    def __init__(self) -> None:
        self._repo = ProfileSettingsRepository()

    @staticmethod
    def _normalize_profile_name(value: str) -> str:
        v = str(value or "").strip()
        if not v:
            raise ValueError("profileName must not be empty")
        return v

    @staticmethod
    def _normalize_nickname(value: str | None) -> str | None:
        if value is None:
            return None
        v = str(value).strip()
        if not v:
            return None
        v = re.sub(r"\s+", "_", v)
        v = re.sub(r"_+", "_", v)
        return v

    @staticmethod
    def _normalize_photo_uri(value: str | None) -> str | None:
        if value is None:
            return None
        v = str(value).strip()
        return v or None

    @staticmethod
    def make_default(*, owner_id: UUID) -> ProfileSettings:
        return ProfileSettings(
            owner_id=owner_id,
            profile_name="Пользователь beze",
            nickname=None,
            photo_uri=None,
        )

    async def get_or_default(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
    ) -> ProfileSettings:
        obj = await self._repo.get_by_owner_id(session, owner_id=owner_id)
        if obj is not None:
            return obj
        return self.make_default(owner_id=owner_id)

    async def patch(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        profile_name: str | None,
        nickname: str | None,
        photo_uri: str | None,
    ) -> ProfileSettings:
        obj = await self._repo.get_by_owner_id(session, owner_id=owner_id)

        if obj is None:
            obj = self.make_default(owner_id=owner_id)
            session.add(obj)

        if profile_name is not None:
            obj.profile_name = self._normalize_profile_name(profile_name)

        if nickname is not None:
            obj.nickname = self._normalize_nickname(nickname)

        if photo_uri is not None:
            obj.photo_uri = self._normalize_photo_uri(photo_uri)

        obj.updated_at = datetime.now(timezone.utc)

        session.add(obj)
        await session.commit()
        return await self.get_or_default(session, owner_id=owner_id)