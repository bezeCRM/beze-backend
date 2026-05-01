from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_session
from app.modules.auth.exceptions import (
    LoginAlreadyExists,
    EmailAlreadyExists,
    InvalidCredentials,
    TokenInvalid,
    TokenRevoked, ResetTokenInvalid,
)
from app.modules.auth.repository import RefreshTokensRepository, PasswordResetTokensRepository
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse, ForgotPasswordRequest, ResetPasswordRequest,
)
from app.modules.auth.service import AuthService
from app.modules.users.repository import UsersRepository

from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService(
        users_repo=UsersRepository(),
        refresh_repo=RefreshTokensRepository(),
        reset_repo=PasswordResetTokensRepository(),
    )


@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    try:
        user = await svc.register(
            session,
            login=data.login,
            email=data.email,         # ← добавить
            password=data.password,
        )
        access_token, refresh_token = await svc.login(
            session,
            credential=user.login,    # ← было login=
            password=data.password,
        )
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
    except LoginAlreadyExists:
        raise HTTPException(status_code=409, detail="login already exists")
    except EmailAlreadyExists:        # ← новый обработчик
        raise HTTPException(status_code=409, detail="email already exists")


@router.post("/login", response_model=TokenPairResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    try:
        access_token, refresh_token = await svc.login(
            session,
            credential=data.credential,  # ← было login=data.login
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

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    data: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> None:
    await svc.forgot_password(session, email=data.email)
    # Всегда 204 — не раскрываем наличие email


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    data: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
    svc: AuthService = Depends(get_auth_service),
) -> None:
    try:
        await svc.reset_password(session, token=data.token, new_password=data.password)
    except ResetTokenInvalid:
        raise HTTPException(status_code=400, detail="invalid or expired token")

@router.get("/reset-password")
async def reset_password_redirect(token: str) -> RedirectResponse:
    return RedirectResponse(url=f"beze://reset-password?token={token}")