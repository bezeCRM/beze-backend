from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.settings import StageEnum, settings

IS_PROD = settings.STAGE == StageEnum.PRODUCTION
app = FastAPI(
    title="FastAPI-starter",
    version="1.0",
    openapi_tags=[],
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
    root_path="/api"
)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
