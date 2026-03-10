"""Dashboard aggregation endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.analysis import Analysis
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.user import User
from app.services.resource_service import get_balance_summary

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取仪表盘聚合数据"""

    uid = current_user.id

    balance_summary = await get_balance_summary(db, str(uid))
    resource_balance = int(balance_summary["resource_balance"])
    subscription = str(balance_summary["plan"])
    used_this_month = int(balance_summary["used_this_month"])
    actual_used_this_month = int(balance_summary["actual_used_this_month"])

    # Project count
    proj_count_result = await db.execute(
        select(func.count(Project.id)).where(Project.owner_id == uid)
    )
    project_count = proj_count_result.scalar() or 0

    # Dataset count
    dataset_count_result = await db.execute(
        select(func.count(Dataset.id))
        .select_from(Dataset)
        .join(Project, Dataset.project_id == Project.id)
        .where(Project.owner_id == uid)
    )
    dataset_count = dataset_count_result.scalar() or 0

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
    recent_projects = []
    for p in recent_proj_result.scalars().all():
        recent_projects.append(
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "updated_at": p.updated_at.isoformat(),
            }
        )

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
        "token_balance": {
            "balance": resource_balance,
            "resource_balance": resource_balance,
            "token_balance": resource_balance,
            "label": "资源",
            "plan": subscription,
            "used_this_month": used_this_month,
            "actual_used_this_month": actual_used_this_month,
        },
        "resource_balance": {
            "balance": resource_balance,
            "resource_balance": resource_balance,
            "used_this_month": used_this_month,
            "actual_used_this_month": actual_used_this_month,
        },
        "usage_stats": {
            "active_projects": project_count,
            "total_datasets": dataset_count,
            "completed_analyses": analysis_count,
        },
        "projects": recent_projects,
        "subscription": subscription,
        "used_this_month": used_this_month,
        "project_count": project_count,
        "dataset_count": dataset_count,
        "analysis_count": analysis_count,
        "recent_projects": recent_projects,
        "recent_analyses": recent_analyses,
    }
