"""Payment service backed by Alipay face-to-face payment APIs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.db.models.order import Order
from app.db.models.user import User
from app.schemas.payment import PaymentCreateRequest
from app.services.alipay_service import (
    AlipayTradeStatus,
    query_trade,
    run_precreate,
    verify_notification_signature,
)


PACKAGE_EXPIRE_MINUTES = 5
PRICE_SCALE = Decimal("0.01")
SUCCESS_STATUSES = {"TRADE_SUCCESS", "TRADE_FINISHED"}
CLOSED_STATUSES = {"TRADE_CLOSED"}
SUBSCRIPTION_BY_PACKAGE = {
    "basic": "basic",
    "pro": "pro",
    "enterprise": "enterprise",
}


@dataclass(frozen=True)
class PackageDefinition:
    id: str
    name: str
    amount: Decimal
    resources: int
    badge: str
    features: Tuple[str, ...]

    @property
    def unit_price(self) -> str:
        return str((self.amount / Decimal(self.resources)).quantize(PRICE_SCALE, rounding=ROUND_HALF_UP))


PACKAGE_CATALOG: Dict[str, PackageDefinition] = {
    "basic": PackageDefinition(
        id="basic",
        name="基础资源包",
        amount=Decimal("0.01"),
        resources=500,
        badge="",
        features=("500 资源点", "描述统计分析", "基础图表生成", "邮件支持"),
    ),
    "pro": PackageDefinition(
        id="pro",
        name="专业资源包",
        amount=Decimal("0.01"),
        resources=2500,
        badge="最受欢迎",
        features=("2,500 资源点", "全部分析方法", "可复现 R 脚本", "优先技术支持"),
    ),
    "enterprise": PackageDefinition(
        id="enterprise",
        name="企业资源包",
        amount=Decimal("0.01"),
        resources=8000,
        badge="",
        features=("8,000 资源点", "定制分析模块", "API 集成接口", "专属技术顾问"),
    ),
}


def _get_package(package_id: str) -> PackageDefinition:
    package = PACKAGE_CATALOG.get(package_id)
    if not package:
        raise BadRequest("无效的套餐类型")
    return package


def _format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}"


def list_packages() -> Iterable[PackageDefinition]:
    return PACKAGE_CATALOG.values()


def _coerce_payment_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _coerce_amount(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None
    try:
        return Decimal(value).quantize(Decimal("0.01"))
    except Exception:
        return None


def _mark_paid(order: Order, user: User, trade: AlipayTradeStatus) -> None:
    if order.status == "paid":
        return
    order.status = "paid"
    order.alipay_trade_no = trade.trade_no or order.alipay_trade_no
    order.paid_at = _coerce_payment_time(trade.paid_at) or datetime.now(timezone.utc)
    user.token_balance += order.tokens
    # Sync plan level with the package user paid for.
    user.subscription = SUBSCRIPTION_BY_PACKAGE.get(order.package_id, user.subscription)


def _apply_trade_status(order: Order, user: User, trade: AlipayTradeStatus) -> bool:
    changed = False

    if trade.total_amount is not None:
        expected = Decimal(order.amount).quantize(Decimal("0.01"))
        actual = _coerce_amount(trade.total_amount)
        if actual is not None and actual != expected:
            raise BadRequest("支付宝返回的订单金额与本地订单不一致")

    if trade.status in SUCCESS_STATUSES:
        before = order.status
        _mark_paid(order, user, trade)
        changed = before != order.status
    elif trade.status in CLOSED_STATUSES and order.status == "pending":
        order.status = "expired"
        changed = True

    return changed


async def create_order(db: AsyncSession, user: User, payload: PaymentCreateRequest) -> Order:
    package = _get_package(payload.packageId)
    expire_at = (datetime.now(timezone.utc) + timedelta(minutes=PACKAGE_EXPIRE_MINUTES)).replace(microsecond=0)

    order = Order(
        user_id=user.id,
        package_id=package.id,
        package_name=package.name,
        amount=package.amount,
        tokens=package.resources,
        status="pending",
        expire_at=expire_at,
    )
    db.add(order)
    await db.flush()

    try:
        precreate = await run_precreate(
            out_trade_no=str(order.id),
            subject=f"MediCode {package.name}",
            total_amount=_format_amount(package.amount),
            timeout_express=f"{PACKAGE_EXPIRE_MINUTES}m",
        )
    except Exception:
        await db.rollback()
        raise

    order.qr_code_url = precreate["qr_code"]
    order.expire_at = expire_at

    await db.commit()
    await db.refresh(order)
    return order


async def get_order_for_user(db: AsyncSession, user: User, order_id: str) -> Order:
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFound("订单不存在")
    return order


async def sync_order_status(db: AsyncSession, user: User, order_id: str) -> Order:
    order = await get_order_for_user(db, user, order_id)
    if order.status == "paid":
        return order

    trade = await query_trade(str(order.id))
    changed = _apply_trade_status(order, user, trade)
    if changed:
        await db.commit()
        await db.refresh(order)
    return order


async def handle_notification(db: AsyncSession, payload: Dict[str, str]) -> Optional[Order]:
    if not verify_notification_signature(payload):
        raise BadRequest("支付宝通知验签失败")

    out_trade_no = payload.get("out_trade_no")
    if not out_trade_no:
        raise BadRequest("支付宝通知缺少 out_trade_no")

    result = await db.execute(select(Order).where(Order.id == out_trade_no))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFound("订单不存在")

    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFound("用户不存在")

    trade = AlipayTradeStatus(
        status=payload.get("trade_status", ""),
        trade_no=payload.get("trade_no"),
        total_amount=payload.get("total_amount"),
        paid_at=payload.get("gmt_payment"),
    )
    changed = _apply_trade_status(order, user, trade)
    if changed:
        await db.commit()
        await db.refresh(order)
    return order


async def list_orders(db: AsyncSession, user: User) -> list[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()
