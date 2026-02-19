from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.settings import StageEnum, settings

IS_PROD = settings.STAGE == StageEnum.PRODUCTION

app = FastAPI(
    title="FastAPI-starter",
    version="1.0",
    openapi_tags=[],
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
    root_path="/api",
)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(v1_router)
