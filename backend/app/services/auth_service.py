"""Auth service — registration, login, verification codes, password reset."""

import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, Forbidden, NotFound, RateLimited, Unauthorized
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User, VerificationCode
from app.services.email_service import send_verification_email


def _random_code() -> str:
    return "".join(random.choices(string.digits, k=6))


# ── Send Code ────────────────────────────────────────────

async def send_code(db: AsyncSession, email: str, purpose: str) -> dict:
    """Generate a 6-digit code, invalidate old ones, persist, and send email."""

    valid_purposes = ("register", "reset-password", "change-password")
    if purpose not in valid_purposes:
        raise BadRequest(f"purpose 必须是 {valid_purposes} 之一")

    # For register: check if email already registered and verified
    if purpose == "register":
        existing = await db.execute(select(User).where(User.email == email, User.is_verified == True))
        if existing.scalar_one_or_none():
            raise Conflict("该邮箱已注册")

    # For reset-password: check email exists
    if purpose == "reset-password":
        existing = await db.execute(select(User).where(User.email == email, User.is_verified == True))
        if not existing.scalar_one_or_none():
            raise NotFound("该邮箱未注册")

    # Rate limit: 60s cooldown per email+purpose
    recent = await db.execute(
        select(VerificationCode)
        .where(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose,
            VerificationCode.created_at > datetime.now(timezone.utc) - timedelta(seconds=60),
        )
        .limit(1)
    )
    if recent.scalar_one_or_none():
        raise RateLimited("发送太频繁，请 60 秒后重试")

    # Invalidate old codes for this email+purpose
    await db.execute(
        update(VerificationCode)
        .where(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False,
        )
        .values(is_used=True)
    )

    # Create new code
    code = _random_code()
    vc = VerificationCode(
        email=email,
        code=code,
        purpose=purpose,
        expire_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(vc)
    await db.flush()

    # Send email (async, best-effort)
    await send_verification_email(email, code, purpose)

    return {"message": "验证码已发送", "expire_seconds": 600}


# ── Verify Code ──────────────────────────────────────────

async def verify_code(db: AsyncSession, email: str, code: str, purpose: str) -> bool:
    """Validate a verification code. Returns True on success."""

    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False,
            VerificationCode.expire_at > datetime.now(timezone.utc),
        )
    )
    vc = result.scalar_one_or_none()
    if not vc:
        raise BadRequest("验证码错误或已过期")

    vc.is_used = True
    await db.flush()
    return True


# ── Register ─────────────────────────────────────────────

async def register(db: AsyncSession, name: str, email: str, password: str, code: str) -> dict:
    """Register a new user. Email must have been verified via verify-code first."""

    # Re-verify code to ensure frontend didn't skip
    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.purpose == "register",
            VerificationCode.code == code,
            VerificationCode.is_used == True,  # should already be marked used by verify-code
        )
    )
    if not result.scalar_one_or_none():
        raise BadRequest("请先完成邮箱验证")

    # Check if email already taken (verified user)
    existing = await db.execute(select(User).where(User.email == email))
    existing_user = existing.scalar_one_or_none()
    if existing_user and existing_user.is_verified:
        raise Conflict("该邮箱已注册")

    # If unverified user exists, overwrite
    if existing_user:
        existing_user.name = name
        existing_user.password_hash = hash_password(password)
        existing_user.is_verified = True
        existing_user.token_balance = 100
        existing_user.updated_at = datetime.now(timezone.utc)
        user = existing_user
    else:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_verified=True,
            token_balance=100,
        )
        db.add(user)

    await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "token_balance": user.token_balance,
            "subscription": user.subscription,
            "is_verified": user.is_verified,
        },
    }


# ── Login ────────────────────────────────────────────────

async def login(db: AsyncSession, email: str, password: str) -> dict:
    """Authenticate user with email + password."""

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise Unauthorized("邮箱或密码错误")

    if not user.is_verified:
        raise Forbidden("邮箱未验证")

    if not user.is_active:
        raise Forbidden("账号已禁用")

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "token_balance": user.token_balance,
            "subscription": user.subscription,
            "is_verified": user.is_verified,
        },
    }


# ── Reset Password ───────────────────────────────────────

async def reset_password(db: AsyncSession, email: str, code: str, new_password: str) -> bool:
    """Reset password after code verification."""

    # Verify code
    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.purpose == "reset-password",
            VerificationCode.is_used == True,
        )
    )
    if not result.scalar_one_or_none():
        raise BadRequest("请先完成邮箱验证")

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFound("用户不存在")

    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return True
