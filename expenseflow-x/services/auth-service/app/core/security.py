"""Auth Service - JWT Token Management with Rotation"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.redis_client import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)


class TokenService:
    """JWT Token management: access, refresh, rotation, blacklisting"""

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        subject: str,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": subject,
            "iat": now,
            "exp": expire,
            "type": "access",
            "jti": secrets.token_urlsafe(16),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(subject: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": subject,
            "iat": now,
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(16),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")

    @staticmethod
    async def blacklist_token(jti: str, expires_in: int = None) -> None:
        """Add a token JTI to the Redis blacklist"""
        ttl = expires_in or (settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        await redis_client.setex(f"token:blacklist:{jti}", ttl, "1")

    @staticmethod
    async def is_token_blacklisted(jti: str) -> bool:
        return await redis_client.exists(f"token:blacklist:{jti}") > 0

    @staticmethod
    async def rotate_refresh_token(old_token: str, subject: str) -> tuple[str, str]:
        """Invalidate old refresh token, issue new pair"""
        payload = TokenService.decode_token(old_token)
        await TokenService.blacklist_token(
            payload["jti"],
            expires_in=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
        )
        access = TokenService.create_access_token(subject, {"roles": payload.get("roles", [])})
        refresh = TokenService.create_refresh_token(subject)
        return access, refresh


token_service = TokenService()
