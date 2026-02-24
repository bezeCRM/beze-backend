from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.schema_utils import to_camel


class ProfileSettingsRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    owner_id: UUID = Field(alias="ownerId")
    profile_name: str = Field(alias="profileName")
    nickname: Optional[str] = None
    photo_uri: Optional[str] = Field(default=None, alias="photoUri")

    updated_at: datetime = Field(alias="updatedAt")


class ProfileSettingsPatch(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    profile_name: Optional[str] = Field(default=None, alias="profileName")
    nickname: Optional[str] = None
    photo_uri: Optional[str] = Field(default=None, alias="photoUri")