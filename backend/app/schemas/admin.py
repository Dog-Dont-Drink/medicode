"""Schemas for admin dashboard and user management."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class AdminOverviewMetric(BaseModel):
    label: str
    value: int | str
    hint: str | None = None


class AdminDailyMetric(BaseModel):
    date: str
    users: int = 0
    token_consumed: int = 0


class AdminDashboardResponse(BaseModel):
    overview: list[AdminOverviewMetric]
    daily_metrics: list[AdminDailyMetric]
    recent_signups: int = 0
    today_token_consumed: int = 0
    today_actual_token_consumed: int = 0
    paid_orders_total: Decimal = Decimal("0.00")


class AdminUserListItem(BaseModel):
    id: str
    name: str
    email: str
    role: str
    subscription: str
    token_balance: int
    is_verified: bool
    is_active: bool
    institution: str | None = None
    title: str | None = None
    created_at: str
    last_login_at: str | None = None
    project_count: int = 0
    dataset_count: int = 0
    billed_tokens_this_month: int = 0
    actual_tokens_this_month: int = 0


class AdminUserUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = Field(default=None, pattern="^(user|admin)$")
    subscription: str | None = None
    token_balance: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_verified: bool | None = None
    institution: str | None = None
    title: str | None = None


class AdminTableColumn(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool = False


class AdminTableInfo(BaseModel):
    name: str
    label: str
    row_count: int = 0


class AdminTableListResponse(BaseModel):
    tables: list[AdminTableInfo]


class AdminTableRowsResponse(BaseModel):
    table_name: str
    primary_key: str
    columns: list[AdminTableColumn]
    rows: list[dict]
    total: int = 0


class AdminTableRowUpdateRequest(BaseModel):
    values: dict
