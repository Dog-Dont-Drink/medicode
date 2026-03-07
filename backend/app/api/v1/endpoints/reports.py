"""Endpoints for saved analysis reports."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.analysis import Analysis, AnalysisResult
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.report import ReportListItemResponse

router = APIRouter(prefix="/reports", tags=["报告"])


@router.get("", response_model=list[ReportListItemResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List saved reports for the current user."""
    result = await db.execute(
        select(Analysis, AnalysisResult, Project, Dataset)
        .join(AnalysisResult, AnalysisResult.analysis_id == Analysis.id)
        .join(Project, Project.id == Analysis.project_id)
        .outerjoin(Dataset, Dataset.id == Analysis.dataset_id)
        .where(
            Analysis.created_by == current_user.id,
            or_(
                Analysis.analysis_type == "table1_interpretation",
                Analysis.analysis_type.like("%_regression_interpretation"),
            ),
            Analysis.status == "completed",
        )
        .order_by(Analysis.executed_at.desc(), Analysis.created_at.desc())
    )

    reports: list[ReportListItemResponse] = []
    for analysis, analysis_result, project, dataset in result.all():
        result_data = analysis_result.result_data or {}
        configuration = analysis.configuration or {}
        reports.append(
            ReportListItemResponse(
                analysis_id=str(analysis.id),
                name=analysis.name or "未命名报告",
                analysis_type=analysis.analysis_type,
                status=analysis.status,
                project_id=str(project.id),
                project_name=project.name,
                dataset_id=str(dataset.id) if dataset else None,
                dataset_name=dataset.name if dataset else None,
                feature_name=result_data.get("feature_name"),
                language=result_data.get("language"),
                model=result_data.get("model"),
                group_variable=configuration.get("group_variable"),
                content=result_data.get("content"),
                prompt_tokens=int(result_data.get("prompt_tokens") or 0),
                completion_tokens=int(result_data.get("completion_tokens") or 0),
                actual_tokens=int(result_data.get("actual_tokens") or result_data.get("llm_tokens_used") or 0),
                billed_tokens=int(result_data.get("billed_tokens") or result_data.get("charged_tokens") or analysis.tokens_consumed or 0),
                created_at=analysis_result.created_at.isoformat() if analysis_result.created_at else analysis.created_at.isoformat(),
                executed_at=analysis.executed_at.isoformat() if analysis.executed_at else None,
            )
        )

    return reports
