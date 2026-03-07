"""User-related Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str = "user"
    phone: str | None = None
    title: str | None = None
    institution: str | None = None
    research_field: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    token_balance: int = 0
    subscription: str = "free"
    is_verified: bool = False
    is_active: bool = True

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    title: str | None = None
    institution: str | None = None
    research_field: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    code: str
    current_password: str
    new_password: str


class BalanceResponse(BaseModel):
    balance: int
    plan: str
    used_this_month: int
    actual_used_this_month: int = 0
