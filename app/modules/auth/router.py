from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_session
from app.modules.auth.exceptions import (
    LoginAlreadyExists,
    InvalidCredentials,
    TokenInvalid,
    TokenRevoked,
)
from app.modules.auth.repository import RefreshTokensRepository
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.repository import UsersRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService(users_repo=UsersRepository(), refresh_repo=RefreshTokensRepository())


@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    try:
        user = await svc.register(session, login=data.login, password=data.password)
        access_token, refresh_token = await svc.login(
            session,
            login=user.login,
            password=data.password,
        )
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
    except LoginAlreadyExists:
        raise HTTPException(status_code=409, detail="login already exists")


@router.post("/login", response_model=TokenPairResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    try:
        access_token, refresh_token = await svc.login(
            session,
            login=data.login,
            password=data.password,
        )
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="invalid credentials")


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_tokens(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    try:
        access_token, refresh_token = await svc.refresh(session, refresh_token=data.refresh_token)
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
    except TokenInvalid:
        raise HTTPException(status_code=401, detail="invalid token")
    except TokenRevoked:
        raise HTTPException(status_code=401, detail="token revoked or expired")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: LogoutRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> None:
    try:
        await svc.logout(session, refresh_token=data.refresh_token)
    except TokenInvalid:
        raise HTTPException(status_code=401, detail="invalid token")
