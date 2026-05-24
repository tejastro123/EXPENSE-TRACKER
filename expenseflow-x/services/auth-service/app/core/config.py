"""Auth Service - Core Configuration (Pydantic v2)"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import List
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # App
    APP_NAME: str = "ExpenseFlow X"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Allowed Origins
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = Field(..., description="Async PostgreSQL connection URL")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")

    # JWT
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password
    BCRYPT_ROUNDS: int = 12

    # OAuth2
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URL: str = "http://localhost:3000/auth/callback"

    # MFA
    TOTP_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    MFA_ISSUER: str = "ExpenseFlowX"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@expenseflowx.com"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # Session
    SESSION_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32))


settings = Settings()
