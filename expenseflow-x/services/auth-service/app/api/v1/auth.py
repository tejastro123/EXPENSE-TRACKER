"""Auth Service - Authentication API Router"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import token_service
from app.core.config import settings
from app.models.user import User, UserStatus, AuditLog
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    TokenResponse, TokenRefreshResponse, MessageResponse,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.email_service import send_verification_email, send_password_reset_email
from app.core.redis_client import redis_client

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency: validate JWT and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = token_service.decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

        if await token_service.is_token_blacklisted(jti):
            raise credentials_exception

    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()

    if user is None or user.status == UserStatus.SUSPENDED:
        raise credentials_exception

    return user


async def log_auth_event(db: AsyncSession, user_id, event: str, request: Request, success: bool, metadata: dict = None):
    """Record auth event in audit log"""
    log = AuditLog(
        user_id=user_id,
        event=event,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=success,
        metadata=metadata or {}
    )
    db.add(log)
    await db.flush()


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register new user with email verification"""
    # Check duplicate
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        hashed_password=token_service.hash_password(payload.password),
        status=UserStatus.PENDING_VERIFICATION,
    )
    db.add(user)
    await db.flush()

    # Send verification email in background
    background_tasks.add_task(send_verification_email, user.email, str(user.id))
    await log_auth_event(db, user.id, "user_registered", request, True)
    await db.commit()

    return MessageResponse(message="Registration successful. Please verify your email.")


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user, return JWT tokens"""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Check lockout
    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=429, detail="Account temporarily locked. Try again later.")

    # Validate credentials
    if not user or not user.hashed_password or not token_service.verify_password(payload.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                from datetime import timedelta
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        await log_auth_event(db, user.id if user else None, "login_failed", request, False)
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=403, detail="Account suspended")

    # MFA verification
    if user.mfa_enabled:
        if not payload.mfa_code:
            raise HTTPException(status_code=202, detail="MFA code required")
        import pyotp
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(payload.mfa_code, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid MFA code")

    # Reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None

    access_token = token_service.create_access_token(str(user.id), {"role": user.role, "email": user.email})
    refresh_token = token_service.create_refresh_token(str(user.id))

    await log_auth_event(db, user.id, "login_success", request, True)
    await db.commit()

    from app.schemas.auth import UserResponse
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_tokens(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Rotate refresh token and issue new access token"""
    try:
        token_data = token_service.decode_token(payload.refresh_token)
        if token_data.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        if await token_service.is_token_blacklisted(token_data["jti"]):
            raise ValueError("Token revoked")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    access, refresh = await token_service.rotate_refresh_token(payload.refresh_token, token_data["sub"])
    return TokenRefreshResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Invalidate current access token"""
    try:
        payload = token_service.decode_token(credentials.credentials)
        await token_service.blacklist_token(payload["jti"])
        await log_auth_event(db, payload.get("sub"), "logout", request, True)
        await db.commit()
    except ValueError:
        pass
    return MessageResponse(message="Successfully logged out")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email"""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        import secrets
        reset_token = secrets.token_urlsafe(32)
        await redis_client.setex(f"pwd_reset:{reset_token}", 3600, str(user.id))
        background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    return MessageResponse(message="If this email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token"""
    user_id = await redis_client.get(f"pwd_reset:{payload.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == user_id.decode()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = token_service.hash_password(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await redis_client.delete(f"pwd_reset:{payload.token}")
    await db.commit()

    return MessageResponse(message="Password reset successfully")


@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify email address"""
    user_id = await redis_client.get(f"email_verify:{token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    result = await db.execute(select(User).where(User.id == user_id.decode()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    user.status = UserStatus.ACTIVE
    await redis_client.delete(f"email_verify:{token}")
    await db.commit()

    return MessageResponse(message="Email verified successfully")
