from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
