from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.users.models import User
from app.modules.users.repository import UsersRepository
from app.modules.users.schemas import UserRead
from app.modules.users.service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


def get_users_service() -> UsersService:
    return UsersService(repo=UsersRepository())


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    svc: UsersService = Depends(get_users_service),
) -> None:
    await svc.delete_current_user(session, current_user)