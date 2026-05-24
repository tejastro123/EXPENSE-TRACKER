from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_NAME: str = "ExpenseFlow X — AI Service"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = Field(..., description="Async PostgreSQL connection URL")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")

    # OpenAI / Pinecone
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = ""

    # Celery
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend")

    # Fraud Threshold
    FRAUD_THRESHOLD: float = 0.85


settings = Settings()
