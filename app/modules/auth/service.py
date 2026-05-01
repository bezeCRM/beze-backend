from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.settings import settings
from app.modules.auth.exceptions import (
    LoginAlreadyExists,
    EmailAlreadyExists,
    InvalidCredentials,
    TokenInvalid,
    TokenRevoked,
)
from app.modules.auth.repository import RefreshTokensRepository
from app.modules.users.repository import UsersRepository
from app.modules.users.models import User

from datetime import timedelta
from app.modules.auth.repository import PasswordResetTokensRepository
from app.modules.auth.exceptions import ResetTokenInvalid
from app.core.email import send_reset_email


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _require_token_type(payload: dict[str, Any], expected: str) -> str:
    t = payload.get("type")
    if t != expected:
        raise TokenInvalid()
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise TokenInvalid()
    return sub


class AuthService:
    def __init__(
            self,
            users_repo: UsersRepository,
            refresh_repo: RefreshTokensRepository,
            reset_repo: PasswordResetTokensRepository,
    ) -> None:
        self._users_repo = users_repo
        self._refresh_repo = refresh_repo
        self._reset_repo = reset_repo

    async def register(
            self,
            session: AsyncSession,
            *,
            login: str,
            email: str,
            password: str,
    ) -> User:
        normalized_login = login.lower().strip()
        normalized_email = email.lower().strip()

        if await self._users_repo.get_by_login(session, normalized_login) is not None:
            raise LoginAlreadyExists()

        if await self._users_repo.get_by_email(session, normalized_email) is not None:
            raise EmailAlreadyExists()

        user = await self._users_repo.create(
            session,
            login=normalized_login,
            email=normalized_email,
            password_hash=hash_password(password),
        )
        await session.commit()
        await session.refresh(user)
        return user

    async def login(
            self,
            session: AsyncSession,
            *,
            credential: str,
            password: str,
    ) -> tuple[str, str]:
        normalized = credential.lower().strip()

        # пробуем по логину, затем по email
        user = await self._users_repo.get_by_login(session, normalized)
        if user is None:
            user = await self._users_repo.get_by_email(session, normalized)
        if user is None:
            raise InvalidCredentials()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentials()

        access_token, refresh_token = await self._issue_token_pair(session, user_id=user.id)
        await session.commit()
        return access_token, refresh_token

    async def refresh(self, session: AsyncSession, *, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise TokenInvalid()

        sub = _require_token_type(payload, "refresh")
        try:
            user_id = UUID(sub)
        except Exception:
            raise TokenInvalid()

        now = utc_now()
        rt_hash = hash_refresh_token(refresh_token)
        active = await self._refresh_repo.get_active_by_hash(session, rt_hash, now)
        if active is None:
            raise TokenRevoked()

        await self._refresh_repo.revoke(session, active, revoked_at=now)

        access, new_refresh = await self._issue_token_pair(session, user_id=user_id, now=now)
        await session.commit()
        return access, new_refresh

    async def logout(self, session: AsyncSession, *, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise TokenInvalid()

        _ = _require_token_type(payload, "refresh")

        now = utc_now()
        rt_hash = hash_refresh_token(refresh_token)
        active = await self._refresh_repo.get_active_by_hash(session, rt_hash, now)
        if active is None:
            return

        await self._refresh_repo.revoke(session, active, revoked_at=now)
        await session.commit()

    async def _issue_token_pair(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        now: datetime | None = None,
    ) -> tuple[str, str]:
        now = now or utc_now()

        access = create_access_token(
            subject=str(user_id),
            expires_minutes=settings.ACCESS_TOKEN_TTL_MINUTES,
        )
        refresh = create_refresh_token(
            subject=str(user_id),
            expires_days=settings.REFRESH_TOKEN_TTL_DAYS,
        )

        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)
        await self._refresh_repo.create(
            session,
            user_id=user_id,
            token_hash=hash_refresh_token(refresh),
            expires_at=expires_at,
        )
        return access, refresh

    async def forgot_password(
            self,
            session: AsyncSession,
            *,
            email: str,
    ) -> None:
        normalized = email.lower().strip()
        user = await self._users_repo.get_by_email(session, normalized)

        # Не раскрываем, существует ли email — просто выходим
        if user is None:
            return

        token = PasswordResetTokensRepository.generate_token()
        token_hash = PasswordResetTokensRepository.hash_token(token)
        now = utc_now()

        await self._reset_repo.create(
            session,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=30),
        )
        await session.commit()

        await send_reset_email(user.email, token)

        print(f"[DEV] token saved hash: '{token_hash}'")

    async def reset_password(
            self,
            session: AsyncSession,
            *,
            token: str,
            new_password: str,
    ) -> None:
        now = utc_now()
        token_hash = PasswordResetTokensRepository.hash_token(token)

        print(f"[DEV] token received: '{token}'")
        print(f"[DEV] token_hash: '{token_hash}'")

        record = await self._reset_repo.get_active_by_hash(session, token_hash, now)

        print(f"[DEV] record found: {record}")

        if record is None:
            raise ResetTokenInvalid()

        user = await self._users_repo.get_by_id(session, record.user_id)
        if user is None:
            raise ResetTokenInvalid()

        await self._users_repo.update_password(session, user, hash_password(new_password))
        await self._reset_repo.mark_used(session, record, now)
        await session.commit()
