from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.modules.auth.router import router as auth_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(auth_router)