from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.profile.schemas import ProfileSettingsPatch, ProfileSettingsRead
from app.modules.profile.service import ProfileSettingsService
from app.modules.users.models import User

router = APIRouter(prefix="/profile/settings", tags=["profile"])


@router.get("", response_model=ProfileSettingsRead)
async def get_settings(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = ProfileSettingsService()
    obj = await svc.get_or_default(session, owner_id=current_user.id)

    return ProfileSettingsRead(
        ownerId=obj.owner_id,
        profileName=obj.profile_name,
        nickname=obj.nickname,
        photoUri=obj.photo_uri,
        updatedAt=obj.updated_at,
    )


@router.patch("", response_model=ProfileSettingsRead)
async def patch_settings(
    payload: ProfileSettingsPatch,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = ProfileSettingsService()
    try:
        obj = await svc.patch(
            session,
            owner_id=current_user.id,
            profile_name=payload.profile_name,
            nickname=payload.nickname,
            photo_uri=payload.photo_uri,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ProfileSettingsRead(
        ownerId=obj.owner_id,
        profileName=obj.profile_name,
        nickname=obj.nickname,
        photoUri=obj.photo_uri,
        updatedAt=obj.updated_at,
    )