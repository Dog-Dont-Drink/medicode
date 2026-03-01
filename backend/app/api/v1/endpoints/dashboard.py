"""Dashboard aggregation endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.analysis import Analysis
from app.db.models.order import TokenUsage
from app.db.models.project import Project
from app.db.models.user import User

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取仪表盘聚合数据"""

    uid = current_user.id

    # Token balance
    token_balance = current_user.token_balance
    subscription = current_user.subscription

    # Used this month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_result = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.tokens_consumed), 0)).where(
            TokenUsage.user_id == uid,
            TokenUsage.created_at >= month_start,
        )
    )
    used_this_month = usage_result.scalar() or 0

    # Project count
    proj_count_result = await db.execute(
        select(func.count(Project.id)).where(Project.owner_id == uid)
    )
    project_count = proj_count_result.scalar() or 0

    # Analysis count (completed)
    analysis_count_result = await db.execute(
        select(func.count(Analysis.id)).where(
            Analysis.created_by == uid,
            Analysis.status == "completed",
        )
    )
    analysis_count = analysis_count_result.scalar() or 0

    # Recent projects (5)
    recent_proj_result = await db.execute(
        select(Project)
        .where(Project.owner_id == uid)
        .order_by(Project.updated_at.desc())
        .limit(5)
    )
    recent_projects = [
        {"id": str(p.id), "name": p.name, "updated_at": p.updated_at.isoformat()}
        for p in recent_proj_result.scalars().all()
    ]

    # Recent analyses (5)
    recent_an_result = await db.execute(
        select(Analysis)
        .where(Analysis.created_by == uid)
        .order_by(Analysis.created_at.desc())
        .limit(5)
    )
    recent_analyses = [
        {
            "id": str(a.id),
            "name": a.name,
            "method": a.analysis_type,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent_an_result.scalars().all()
    ]

    return {
        "token_balance": token_balance,
        "subscription": subscription,
        "used_this_month": used_this_month,
        "project_count": project_count,
        "analysis_count": analysis_count,
        "recent_projects": recent_projects,
        "recent_analyses": recent_analyses,
    }
