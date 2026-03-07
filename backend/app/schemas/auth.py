"""Auth-related Pydantic schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Requests ──────────────────────────────────────────────

class SendCodeRequest(BaseModel):
    email: EmailStr
    purpose: str  # register | reset-password | change-password


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str
    purpose: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    code: str  # 前端已验证过的验证码，后端再次校验


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Responses ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    expire_seconds: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserBrief"


class UserBrief(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: str | None = None
    role: str = "user"
    token_balance: int = 0
    subscription: str = "free"
    is_verified: bool = False

    model_config = {"from_attributes": True}


class VerifyCodeResponse(BaseModel):
    verified: bool


class NeedVerifyResponse(BaseModel):
    error: str
    need_verify: bool = True
    email: str
