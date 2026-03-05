"""Dataset API endpoints."""

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import BadRequest, Forbidden, NotFound
from app.db.database import get_db
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.dataset import DatasetResponse
from app.services.storage_service import storage_service

router = APIRouter(prefix="/datasets", tags=["数据集"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".sav", ".dta"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传数据文件"""
    # Validate project ownership
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("项目不存在")
    if project.owner_id != current_user.id:
        raise Forbidden("无权操作该项目")

    # Validate file
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequest(f"不支持的文件格式，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise BadRequest("文件大小不能超过 50MB")

    file_id = uuid.uuid4()
    object_key = f"{current_user.id}/{project_id}/{file_id}{ext}"
    await storage_service.upload(
        object_key=object_key,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )

    dataset = Dataset(
        project_id=uuid.UUID(project_id),
        name=file.filename or "unnamed",
        file_path=object_key,
        file_size=len(content),
        file_format=ext.lstrip("."),
        uploaded_by=current_user.id,
    )
    try:
        db.add(dataset)
        await db.flush()
    except Exception:
        await storage_service.delete(object_key)
        raise

    return DatasetResponse(
        id=str(dataset.id),
        name=dataset.name,
        file_size=dataset.file_size,
        file_format=dataset.file_format,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        created_at=dataset.created_at,
    )


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目下的数据集列表"""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.project_id == project_id)
        .order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()
    return [
        DatasetResponse(
            id=str(ds.id),
            name=ds.name,
            file_size=ds.file_size,
            file_format=ds.file_format,
            row_count=ds.row_count,
            column_count=ds.column_count,
            created_at=ds.created_at,
        )
        for ds in datasets
    ]


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除数据集"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise NotFound("数据集不存在")

    # Check project ownership
    proj_result = await db.execute(select(Project).where(Project.id == dataset.project_id))
    project = proj_result.scalar_one_or_none()
    if not project or project.owner_id != current_user.id:
        raise Forbidden("无权操作")

    await storage_service.delete(dataset.file_path)

    await db.delete(dataset)
    await db.flush()
    return {"success": True}
