from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_NAME: str = "ExpenseFlow X — Expense Service"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = Field(..., description="Async PostgreSQL connection URL")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")

    # Celery
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")

    # AWS S3 (for receipt storage)
    S3_BUCKET_NAME: str = "expenseflow-receipts"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"


settings = Settings()
