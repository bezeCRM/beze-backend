from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class StageEnum(str, Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    LOCAL = "LOCAL"


class Settings(BaseSettings):
    POSTGRES_DSN: str = "postgresql+asyncpg://user:password@localhost/dbname"
    STAGE: StageEnum = StageEnum.LOCAL

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()