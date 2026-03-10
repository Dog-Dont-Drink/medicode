"""Admin-only dashboard and user management endpoints."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import MetaData, Table, delete, func, inspect, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.exceptions import BadRequest, Conflict, NotFound
from app.db.database import get_db
from app.db.models.dataset import Dataset
from app.db.models.order import Order, TokenUsage
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminDailyMetric,
    AdminOverviewMetric,
    AdminTableColumn,
    AdminTableInfo,
    AdminTableListResponse,
    AdminTableRowUpdateRequest,
    AdminTableRowsResponse,
    AdminUserListItem,
    AdminUserUpdateRequest,
)

router = APIRouter(prefix="/admin", tags=["管理员后台"])
TABLE_LABELS = {
    "users": "用户表",
    "verification_codes": "验证码",
    "projects": "项目表",
    "datasets": "数据集",
    "dataset_dictionary": "数据字典",
    "analyses": "分析任务",
    "analysis_results": "分析结果",
    "orders": "订单记录",
    "token_usage": "资源消耗",
}


def _utc_today_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_value(value):
    if isinstance(value, datetime):
        value = _normalize_datetime(value)
        return value.isoformat() if value else None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


async def _reflect_table(db: AsyncSession, table_name: str) -> Table:
    async with db.bind.begin() as conn:
        return await conn.run_sync(
            lambda sync_conn: Table(table_name, MetaData(), autoload_with=sync_conn)
        )


async def _get_table_names(db: AsyncSession) -> list[str]:
    async with db.bind.begin() as conn:
        return await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())


def _coerce_update_value(column, value):
    if value is None:
        return None

    column_type = getattr(column.type, "python_type", None)
    if column_type is None:
        return value

    try:
        if column_type is bool:
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in {"1", "true", "yes", "on"}
        if column_type is int:
            return int(value)
        if column_type is float:
            return float(value)
        if column_type is Decimal:
            return Decimal(str(value))
        if column_type is datetime:
            parsed = datetime.fromisoformat(str(value))
            return _normalize_datetime(parsed)
        if column_type is uuid.UUID:
            return str(uuid.UUID(str(value)))
        return column_type(value)
    except Exception:
        return value


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return admin operational overview and daily trends."""
    del current_admin

    today_start, tomorrow_start = _utc_today_range()
    seven_days_ago = today_start - timedelta(days=6)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (
        await db.execute(select(func.count(User.id)).where(User.is_active == True))
    ).scalar() or 0
    paid_users = (
        await db.execute(select(func.count(User.id)).where(User.subscription != "free"))
    ).scalar() or 0
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0

    recent_users = (
        await db.execute(
            select(User.created_at).where(User.created_at >= seven_days_ago)
        )
    ).scalars().all()
    recent_token_usage = (
        await db.execute(
            select(TokenUsage.created_at, TokenUsage.tokens_consumed, TokenUsage.actual_tokens_consumed)
            .where(TokenUsage.created_at >= seven_days_ago)
        )
    ).all()

    recent_signups = sum(
        1 for created_at in recent_users
        if (normalized := _normalize_datetime(created_at)) and normalized >= today_start
    )
    today_token_consumed = sum(
        row.tokens_consumed
        for row in recent_token_usage
        if (normalized := _normalize_datetime(row.created_at)) and normalized >= today_start
    )
    today_actual_token_consumed = sum(
        row.actual_tokens_consumed
        for row in recent_token_usage
        if (normalized := _normalize_datetime(row.created_at)) and normalized >= today_start
    )

    paid_orders_total = (
        await db.execute(
            select(func.coalesce(func.sum(Order.amount), 0))
            .where(Order.status == "paid")
        )
    ).scalar() or Decimal("0.00")

    user_counts_by_day: dict[date, int] = defaultdict(int)
    for created_at in recent_users:
        normalized = _normalize_datetime(created_at)
        if normalized:
            user_counts_by_day[normalized.date()] += 1

    token_counts_by_day: dict[date, int] = defaultdict(int)
    for usage in recent_token_usage:
        normalized = _normalize_datetime(usage.created_at)
        if normalized:
            token_counts_by_day[normalized.date()] += int(usage.tokens_consumed or 0)

    daily_metrics: list[AdminDailyMetric] = []
    for offset in range(7):
        current_day = seven_days_ago.date() + timedelta(days=offset)
        daily_metrics.append(
            AdminDailyMetric(
                date=current_day.isoformat(),
                users=user_counts_by_day[current_day],
                token_consumed=token_counts_by_day[current_day],
            )
        )

    overview = [
        AdminOverviewMetric(label="总用户数", value=int(total_users), hint=f"活跃 {int(active_users)}"),
        AdminOverviewMetric(label="今日新增", value=int(recent_signups), hint="按 UTC+0 统计"),
        AdminOverviewMetric(label="付费用户", value=int(paid_users), hint=f"项目总数 {int(total_projects)}"),
        AdminOverviewMetric(label="今日资源消耗", value=int(today_token_consumed), hint=f"模型实际 {int(today_actual_token_consumed)}"),
        AdminOverviewMetric(label="累计收入", value=f"{Decimal(paid_orders_total):.2f}", hint="已支付订单"),
    ]

    return AdminDashboardResponse(
        overview=overview,
        daily_metrics=daily_metrics,
        recent_signups=int(recent_signups),
        today_token_consumed=int(today_token_consumed),
        today_actual_token_consumed=int(today_actual_token_consumed),
        paid_orders_total=Decimal(paid_orders_total),
    )


@router.get("/tables", response_model=AdminTableListResponse)
async def list_admin_tables(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List available database tables for generic admin management."""
    del current_admin
    table_names = [name for name in await _get_table_names(db) if not name.startswith("sqlite_")]
    table_infos: list[AdminTableInfo] = []

    for table_name in sorted(table_names):
        table = await _reflect_table(db, table_name)
        row_count = (await db.execute(select(func.count()).select_from(table))).scalar() or 0
        table_infos.append(
            AdminTableInfo(
                name=table_name,
                label=TABLE_LABELS.get(table_name, table_name.replace("_", " ").title()),
                row_count=int(row_count),
            )
        )

    return AdminTableListResponse(tables=table_infos)


@router.get("/tables/{table_name}", response_model=AdminTableRowsResponse)
async def get_admin_table_rows(
    table_name: str,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return rows and column metadata for a database table."""
    del current_admin
    table_names = await _get_table_names(db)
    if table_name not in table_names:
        raise NotFound("数据表不存在")

    table = await _reflect_table(db, table_name)
    primary_keys = [column.name for column in table.primary_key.columns]
    if not primary_keys:
        raise BadRequest("该数据表没有主键，当前后台不支持编辑")

    total = (await db.execute(select(func.count()).select_from(table))).scalar() or 0
    rows = (
        await db.execute(select(table).limit(max(1, min(limit, 200))))
    ).mappings().all()

    return AdminTableRowsResponse(
        table_name=table_name,
        primary_key=primary_keys[0],
        columns=[
            AdminTableColumn(
                name=column.name,
                type=str(column.type),
                nullable=bool(column.nullable),
                primary_key=bool(column.primary_key),
            )
            for column in table.columns
        ],
        rows=[
            {key: _serialize_value(value) for key, value in row.items()}
            for row in rows
        ],
        total=int(total),
    )


@router.put("/tables/{table_name}/rows/{row_id}")
async def update_admin_table_row(
    table_name: str,
    row_id: str,
    body: AdminTableRowUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a row in any database table that has a simple primary key."""
    del current_admin
    table_names = await _get_table_names(db)
    if table_name not in table_names:
        raise NotFound("数据表不存在")

    table = await _reflect_table(db, table_name)
    primary_keys = [column.name for column in table.primary_key.columns]
    if len(primary_keys) != 1:
        raise BadRequest("当前只支持单主键数据表")
    pk_name = primary_keys[0]
    pk_column = table.c[pk_name]

    values = {
        key: _coerce_update_value(table.c[key], value)
        for key, value in body.values.items()
        if key in table.c and key != pk_name
    }
    if not values:
        raise BadRequest("没有可更新的字段")

    pk_value = _coerce_update_value(pk_column, row_id)
    result = await db.execute(
        update(table)
        .where(pk_column == pk_value)
        .values(**values)
    )
    if not result.rowcount:
        raise NotFound("目标记录不存在")

    row = (
        await db.execute(select(table).where(pk_column == pk_value))
    ).mappings().first()
    return {"success": True, "row": {key: _serialize_value(value) for key, value in row.items()}}


@router.delete("/tables/{table_name}/rows/{row_id}")
async def delete_admin_table_row(
    table_name: str,
    row_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a row from any database table that has a simple primary key."""
    del current_admin
    table_names = await _get_table_names(db)
    if table_name not in table_names:
        raise NotFound("数据表不存在")

    table = await _reflect_table(db, table_name)
    primary_keys = [column.name for column in table.primary_key.columns]
    if len(primary_keys) != 1:
        raise BadRequest("当前只支持单主键数据表")
    pk_column = table.c[primary_keys[0]]
    pk_value = _coerce_update_value(pk_column, row_id)

    result = await db.execute(delete(table).where(pk_column == pk_value))
    if not result.rowcount:
        raise NotFound("目标记录不存在")
    return {"success": True}


@router.get("/users", response_model=list[AdminUserListItem])
async def list_admin_users(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List users with operational metadata for admin management."""
    del current_admin

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    project_counts = {
        str(user_id): count
        for user_id, count in (
            await db.execute(
                select(Project.owner_id, func.count(Project.id))
                .group_by(Project.owner_id)
            )
        ).all()
    }
    dataset_counts = {
        str(owner_id): count
        for owner_id, count in (
            await db.execute(
                select(Project.owner_id, func.count(Dataset.id))
                .select_from(Dataset)
                .join(Project, Project.id == Dataset.project_id)
                .group_by(Project.owner_id)
            )
        ).all()
    }
    token_usage_by_user: dict[str, tuple[int, int]] = {
        str(user_id): (billed, actual)
        for user_id, billed, actual in (
            await db.execute(
                select(
                    TokenUsage.user_id,
                    func.coalesce(func.sum(TokenUsage.tokens_consumed), 0),
                    func.coalesce(func.sum(TokenUsage.actual_tokens_consumed), 0),
                )
                .where(TokenUsage.created_at >= month_start)
                .group_by(TokenUsage.user_id)
            )
        ).all()
    }

    users = (
        await db.execute(select(User).order_by(User.created_at.desc()))
    ).scalars().all()

    return [
        AdminUserListItem(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            subscription=user.subscription,
            token_balance=int(user.token_balance or 0),
            is_verified=bool(user.is_verified),
            is_active=bool(user.is_active),
            institution=user.institution,
            title=user.title,
            created_at=user.created_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            project_count=int(project_counts.get(str(user.id), 0)),
            dataset_count=int(dataset_counts.get(str(user.id), 0)),
            billed_tokens_this_month=int(token_usage_by_user.get(str(user.id), (0, 0))[0]),
            actual_tokens_this_month=int(token_usage_by_user.get(str(user.id), (0, 0))[1]),
        )
        for user in users
    ]


@router.put("/users/{user_id}", response_model=AdminUserListItem)
async def update_admin_user(
    user_id: str,
    body: AdminUserUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile and operational fields from admin panel."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        raise BadRequest("用户标识无效") from exc

    user = (
        await db.execute(select(User).where(User.id == user_uuid))
    ).scalar_one_or_none()
    if not user:
        raise NotFound("用户不存在")

    updates = body.model_dump(exclude_unset=True)
    email = updates.get("email")
    if email and email != user.email:
        existing = (
            await db.execute(select(User.id).where(User.email == email, User.id != user.id))
        ).scalar_one_or_none()
        if existing:
            raise Conflict("该邮箱已被其他用户使用")

    for key, value in updates.items():
        setattr(user, key, value)

    if user.id == current_admin.id and user.role != "admin":
        raise BadRequest("不能取消当前管理员自己的 admin 权限")

    user.updated_at = datetime.now(timezone.utc)
    await db.flush()

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    project_count = (
        await db.execute(select(func.count(Project.id)).where(Project.owner_id == user.id))
    ).scalar() or 0
    dataset_count = (
        await db.execute(
            select(func.count(Dataset.id))
            .select_from(Dataset)
            .join(Project, Project.id == Dataset.project_id)
            .where(Project.owner_id == user.id)
        )
    ).scalar() or 0
    token_usage = (
        await db.execute(
            select(
                func.coalesce(func.sum(TokenUsage.tokens_consumed), 0),
                func.coalesce(func.sum(TokenUsage.actual_tokens_consumed), 0),
            ).where(
                TokenUsage.user_id == user.id,
                TokenUsage.created_at >= month_start,
            )
        )
    ).one()

    return AdminUserListItem(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        subscription=user.subscription,
        token_balance=int(user.token_balance or 0),
        is_verified=bool(user.is_verified),
        is_active=bool(user.is_active),
        institution=user.institution,
        title=user.title,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        project_count=int(project_count),
        dataset_count=int(dataset_count),
        billed_tokens_this_month=int(token_usage[0] or 0),
        actual_tokens_this_month=int(token_usage[1] or 0),
    )
