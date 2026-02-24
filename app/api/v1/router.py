from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.modules.users.router import router as users_router
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.products.router import router as products_router
from app.modules.orders.router import router as orders_router
from app.modules.planner.router import router as planner_router
from app.modules.profile.router import router as profile_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(categories_router)
router.include_router(products_router)
router.include_router(orders_router)
router.include_router(planner_router)
router.include_router(profile_router)
