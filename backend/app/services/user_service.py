"""User service — profile, password change, balance."""

from datetime import datetime, timezone
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.core.security import hash_password, verify_password
from app.db.models.order import Order, TokenUsage
from app.db.models.user import User, VerificationCode

SUBSCRIPTION_BY_PACKAGE = {
    "basic": "basic",
    "pro": "pro",
    "enterprise": "enterprise",
}
AI_INTERPRETATION_BASE_FEE = 1000
AI_INTERPRETATION_MULTIPLIER = 1.8


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

    # Reconcile plan from latest paid order so legacy users no longer stay "free".
    latest_paid_order = await db.execute(
        select(Order.package_id)
        .where(
            Order.user_id == user_id,
            Order.status == "paid",
        )
        .order_by(Order.paid_at.desc(), Order.created_at.desc())
        .limit(1)
    )
    package_id = latest_paid_order.scalar_one_or_none()
    if package_id:
        inferred_subscription = SUBSCRIPTION_BY_PACKAGE.get(package_id)
        if inferred_subscription and user.subscription != inferred_subscription:
            user.subscription = inferred_subscription
            await db.flush()

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
    actual_result = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.actual_tokens_consumed), 0)).where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= month_start,
        )
    )
    actual_used = actual_result.scalar()

    return {
        "balance": user.token_balance,
        "plan": user.subscription,
        "used_this_month": used or 0,
        "actual_used_this_month": actual_used or 0,
    }


def calculate_ai_interpretation_charge(llm_tokens_used: int) -> int:
    normalized_llm_tokens = max(int(llm_tokens_used), 0)
    return int(math.ceil(normalized_llm_tokens * AI_INTERPRETATION_MULTIPLIER + AI_INTERPRETATION_BASE_FEE))


async def consume_user_tokens(
    db: AsyncSession,
    user: User,
    operation: str,
    billed_tokens: int,
    actual_tokens: int = 0,
) -> int:
    billed_tokens = max(int(billed_tokens), 0)
    actual_tokens = max(int(actual_tokens), 0)
    if billed_tokens <= 0:
        return int(user.token_balance or 0)

    if (user.token_balance or 0) < billed_tokens:
        raise BadRequest("Token 余额不足，请先充值后再使用 AI 结果解读")

    user.token_balance -= billed_tokens
    user.updated_at = datetime.now(timezone.utc)
    db.add(
        TokenUsage(
            user_id=user.id,
            operation=operation,
            tokens_consumed=billed_tokens,
            actual_tokens_consumed=actual_tokens,
        )
    )
    await db.flush()
    return int(user.token_balance)
