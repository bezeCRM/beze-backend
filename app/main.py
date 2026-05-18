from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.settings import StageEnum, settings

IS_PROD = settings.STAGE == StageEnum.PRODUCTION

MEDIA_DIR = Path("/app/media")

app = FastAPI(
    title="FastAPI-starter",
    version="1.0",
    openapi_tags=[],
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_headers=["*"],
    allow_methods=["*"],
)

(MEDIA_DIR / "profile").mkdir(parents=True, exist_ok=True)
(MEDIA_DIR / "products").mkdir(parents=True, exist_ok=True)
(MEDIA_DIR / "orders" / "references").mkdir(parents=True, exist_ok=True)

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

app.include_router(v1_router)