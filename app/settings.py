from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class StageEnum(str, Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    LOCAL = "LOCAL"


class Settings(BaseSettings):
    POSTGRES_DSN: str = "postgresql+asyncpg://user:password@localhost/dbname"
    STAGE: StageEnum = StageEnum.LOCAL

    JWT_SECRET: str = "dev-insecure-secret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 30

    model_config = SettingsConfigDict(env_file=".env")

    APP_SCHEME: str = "beze"  # deep link scheme из app.json

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None


settings = Settings()