"""User service — profile, password change, balance."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.core.security import hash_password, verify_password
from app.db.models.order import TokenUsage
from app.db.models.user import User, VerificationCode


async def get_profile(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFound("用户不存在")
    return user


async def update_profile(db: AsyncSession, user_id: str, data: dict) -> User:
    user = await get_profile(db, user_id)
    for key, value in data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return user


async def change_password(
    db: AsyncSession,
    user_id: str,
    email: str,
    code: str,
    current_password: str,
    new_password: str,
) -> bool:
    """Change password after email verification code validation."""

    # Verify code was used
    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.purpose == "change-password",
            VerificationCode.is_used == True,
        )
    )
    if not result.scalar_one_or_none():
        raise BadRequest("请先完成邮箱验证")

    user = await get_profile(db, user_id)

    if not verify_password(current_password, user.password_hash):
        raise BadRequest("当前密码错误")

    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return True


async def get_balance(db: AsyncSession, user_id: str) -> dict:
    user = await get_profile(db, user_id)

    # Current month usage
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.tokens_consumed), 0)).where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= month_start,
        )
    )
    used = result.scalar()

    return {
        "balance": user.token_balance,
        "plan": user.subscription,
        "used_this_month": used or 0,
    }
