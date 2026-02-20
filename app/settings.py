from enum import Enum
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


settings = Settings()