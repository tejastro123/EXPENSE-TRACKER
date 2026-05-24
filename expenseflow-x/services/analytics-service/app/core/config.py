from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_NAME: str = "ExpenseFlow X — Analytics Service"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = Field(..., description="Async PostgreSQL connection URL")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")


settings = Settings()
