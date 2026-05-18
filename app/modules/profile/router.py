from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.profile.schemas import (
    ProfileSettingsPatch,
    ProfileSettingsRead,
    ProfilePhotoUploadRead,
)
from app.modules.profile.service import ProfileSettingsService
from app.modules.users.models import User

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request

router = APIRouter(prefix="/profile/settings", tags=["profile"])

ALLOWED_PROFILE_PHOTO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}

MAX_PROFILE_PHOTO_BYTES = 5 * 1024 * 1024
PROFILE_PHOTOS_DIR = Path("media/profile")


@router.post("/photo", response_model=ProfilePhotoUploadRead)
async def upload_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content_type = file.content_type or ""

    if content_type not in ALLOWED_PROFILE_PHOTO_TYPES:
        raise HTTPException(status_code=400, detail="unsupported image type")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    if len(content) > MAX_PROFILE_PHOTO_BYTES:
        raise HTTPException(status_code=400, detail="file is too large")

    PROFILE_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    ext = ALLOWED_PROFILE_PHOTO_TYPES[content_type]
    filename = f"{current_user.id}-{uuid4().hex}{ext}"
    path = PROFILE_PHOTOS_DIR / filename

    path.write_bytes(content)

    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")

    if not host:
        raise HTTPException(status_code=500, detail="host header is missing")

    base_url = f"{proto}://{host}".rstrip("/")
    photo_uri = f"{base_url}/api/media/profile/{filename}"

    return ProfilePhotoUploadRead(photo_uri=photo_uri)

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