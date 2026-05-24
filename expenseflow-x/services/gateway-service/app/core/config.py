from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Microservice URLs
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    EXPENSE_SERVICE_URL: str = "http://expense-service:8002"
    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8003"
    AI_SERVICE_URL: str = "http://ai-service:8004"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"
    ADMIN_SERVICE_URL: str = "http://admin-service:8006"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Gateway Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # JWT key to validate requests at gateway level
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))


settings = Settings()
