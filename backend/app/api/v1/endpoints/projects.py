"""Project API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import Forbidden, NotFound
from app.db.database import get_db
from app.db.models.analysis import Analysis
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["项目"])


@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的项目列表"""
    # Sub-query for dataset count
    ds_count = (
        select(func.count(Dataset.id))
        .where(Dataset.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )
    # Sub-query for analysis count
    an_count = (
        select(func.count(Analysis.id))
        .where(Analysis.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )

    result = await db.execute(
        select(Project, ds_count.label("dataset_count"), an_count.label("analysis_count"))
        .where(Project.owner_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )

    items = []
    for row in result.all():
        proj = row[0]
        items.append(
            ProjectListItem(
                id=str(proj.id),
                name=proj.name,
                description=proj.description,
                study_type=proj.study_type,
                status=proj.status,
                dataset_count=row[1] or 0,
                analysis_count=row[2] or 0,
                updated_at=proj.updated_at,
            )
        )
    return items


@router.post("", response_model=ProjectResponse)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新项目"""
    project = Project(
        owner_id=current_user.id,
        name=body.name,
        study_type=body.study_type,
        description=body.description,
    )
    db.add(project)
    await db.flush()
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        study_type=project.study_type,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("项目不存在")
    if project.owner_id != current_user.id:
        raise Forbidden("无权访问该项目")
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        study_type=project.study_type,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("项目不存在")
    if project.owner_id != current_user.id:
        raise Forbidden("无权修改该项目")

    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        study_type=project.study_type,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除项目（级联删除关联数据）"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("项目不存在")
    if project.owner_id != current_user.id:
        raise Forbidden("无权删除该项目")

    await db.delete(project)
    await db.flush()
    return {"success": True}
