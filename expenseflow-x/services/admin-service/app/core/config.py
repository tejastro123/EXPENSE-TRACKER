from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    ALLOWED_ORIGINS: List[str] = Field(default=["*"])
    ADMIN_SECRET_KEY: str = Field(default="admin_secret_key_change_me")
    DATABASE_URL: str = Field(default="postgresql+asyncpg://expenseflow:password@postgres:5432/expenseflowx")
    REDIS_URL: str = Field(default="redis://:password@redis:6379/0")

settings = Settings()
