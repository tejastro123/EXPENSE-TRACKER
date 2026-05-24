"""Auth Service - Pydantic v2 Schemas"""
from datetime import datetime
from typing import Optional, List
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import re


# ── Request Schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class MFASetupRequest(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)


class MFAVerifyRequest(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)


# ── Response Schemas ────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    username: Optional[str]
    full_name: str
    phone_number: Optional[str]
    avatar_url: Optional[str]
    role: str
    status: str
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MFASetupResponse(BaseModel):
    qr_code_url: str
    secret: str
    backup_codes: List[str]


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[dict]
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime
