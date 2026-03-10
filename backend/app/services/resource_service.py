"""Resource billing and usage helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequest, Forbidden
from app.db.models.order import TokenUsage
from app.db.models.user import User


PaidFeature = Literal["ai_interpretation", "pdf_export"]

PAID_SUBSCRIPTIONS = frozenset({"basic", "pro", "enterprise"})


def get_resource_balance(user: User) -> int:
    return int(user.token_balance or 0)


def resource_fields(balance: int) -> dict[str, int]:
    normalized = max(int(balance), 0)
    return {
        "resource_balance": normalized,
        "token_balance": normalized,
    }


def get_feature_cost(feature: PaidFeature) -> int:
    settings = get_settings()
    if feature == "pdf_export":
        return max(int(settings.PDF_EXPORT_RESOURCE_COST), 0)
    return max(int(settings.AI_INTERPRETATION_RESOURCE_COST), 0)


def _feature_label(feature: PaidFeature) -> str:
    if feature == "pdf_export":
        return "PDF 导出"
    return "AI结果解读"


def ensure_paid_feature_access(user: User, feature: PaidFeature) -> None:
    if user.subscription not in PAID_SUBSCRIPTIONS:
        raise Forbidden(f"{_feature_label(feature)}为付费功能，请升级后使用")


def ensure_sufficient_resources(user: User, feature: PaidFeature) -> int:
    cost = get_feature_cost(feature)
    if get_resource_balance(user) < cost:
        resource_label = get_settings().RESOURCE_LABEL
        raise BadRequest(f"{resource_label}余额不足，{_feature_label(feature)}至少需要 {cost} {resource_label}")
    return cost


async def consume_user_resources(
    db: AsyncSession,
    user: User,
    operation: str,
    billed_resources: int,
    actual_tokens: int = 0,
) -> int:
    billed_resources = max(int(billed_resources), 0)
    actual_tokens = max(int(actual_tokens), 0)
    if billed_resources <= 0:
        return get_resource_balance(user)

    if get_resource_balance(user) < billed_resources:
        resource_label = get_settings().RESOURCE_LABEL
        raise BadRequest(f"{resource_label}余额不足，请先充值后再继续使用")

    user.token_balance -= billed_resources
    user.updated_at = datetime.now(timezone.utc)
    db.add(
        TokenUsage(
            user_id=user.id,
            operation=operation,
            tokens_consumed=billed_resources,
            actual_tokens_consumed=actual_tokens,
        )
    )
    await db.flush()
    return get_resource_balance(user)


async def get_balance_summary(db: AsyncSession, user_id: str) -> dict[str, int | str]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    billed_usage = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.tokens_consumed), 0)).where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= month_start,
        )
    )
    actual_usage = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.actual_tokens_consumed), 0)).where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= month_start,
        )
    )

    used_this_month = int(billed_usage.scalar() or 0)
    actual_used_this_month = int(actual_usage.scalar() or 0)
    balance = get_resource_balance(user)
    return {
        "balance": balance,
        "resource_balance": balance,
        "plan": user.subscription,
        "used_this_month": used_this_month,
        "actual_used_this_month": actual_used_this_month,
    }
