"""Dataset API endpoints."""

import os
import uuid
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import BadRequest, Forbidden, NotFound
from app.db.database import get_db
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.dataset import (
    ColumnSummaryResponse,
    DatasetCleaningRequest,
    DatasetCleaningResultResponse,
    DatasetColumnKindUpdateRequest,
    DatasetColumnKindUpdateResponse,
    DatasetResponse,
    DatasetSummaryResponse,
    PreviewResponse,
    ValueFrequencyResponse,
)
from app.services.data_cleaning_service import clean_dataset_content
from app.services.dataset_parser import parse_tabular_content, summarize_tabular_content
from app.services.dataset_kind_service import get_dataset_kind_overrides, normalize_dataset_kind, update_dataset_kind_override
from app.services.storage_service import storage_service

router = APIRouter(prefix="/datasets", tags=["数据集"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
PAID_SUBSCRIPTIONS = {"basic", "pro", "enterprise"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
FREE_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
FREE_MAX_ROW_COUNT = 200


async def _get_project_for_user(project_id: str, current_user: User, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("项目不存在")
    if project.owner_id != current_user.id:
        raise Forbidden("无权操作该项目")
    return project


async def _get_dataset_for_user(dataset_id: uuid.UUID, current_user: User, db: AsyncSession) -> Dataset:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise NotFound("数据集不存在")

    proj_result = await db.execute(select(Project).where(Project.id == dataset.project_id))
    project = proj_result.scalar_one_or_none()
    if not project or project.owner_id != current_user.id:
        raise Forbidden("无权查看该数据集")
    return dataset


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传数据文件"""
    # Validate project ownership
    await _get_project_for_user(project_id, current_user, db)

    # Validate file
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        supported_formats = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise BadRequest(f"不支持的文件格式，仅支持 {supported_formats}")

    content = await file.read()
    if not content:
        raise BadRequest("上传文件为空")
    is_paid_user = current_user.subscription in PAID_SUBSCRIPTIONS
    max_file_size = MAX_FILE_SIZE if is_paid_user else FREE_MAX_FILE_SIZE
    if len(content) > max_file_size:
        if is_paid_user:
            raise BadRequest("文件大小不能超过 50MB")
        raise BadRequest("免费版单个文件大小不能超过 5MB，请升级付费套餐后上传更大文件。")

    # Validate tabular content before uploading to object storage.
    try:
        parsed = parse_tabular_content(
            content,
            ext,
            preview_rows=5,
            max_rows=None if is_paid_user else FREE_MAX_ROW_COUNT,
        )
    except ValueError as exc:
        raise BadRequest(str(exc))

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
        row_count=parsed.total_rows,
        column_count=parsed.total_columns,
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
    await _get_project_for_user(project_id, current_user, db)

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


@router.get("/{dataset_id}/preview", response_model=PreviewResponse)
async def preview_dataset(
    dataset_id: uuid.UUID,
    rows: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取数据集预览（默认前 5 行）。"""
    if rows < 1 or rows > 100:
        raise BadRequest("rows 参数必须在 1 到 100 之间")

    dataset = await _get_dataset_for_user(dataset_id, current_user, db)

    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    try:
        parsed = parse_tabular_content(content, ext, preview_rows=rows)
    except ValueError as exc:
        raise BadRequest(str(exc))

    return PreviewResponse(
        columns=parsed.columns,
        rows=parsed.rows,
        total_rows=parsed.total_rows,
        total_columns=parsed.total_columns,
    )


@router.get("/{dataset_id}/summary", response_model=DatasetSummaryResponse)
async def summarize_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取数据集基础统计摘要。"""
    dataset = await _get_dataset_for_user(dataset_id, current_user, db)

    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    try:
        overrides = await get_dataset_kind_overrides(db, str(dataset.id))
        summary = summarize_tabular_content(content, ext, kind_overrides=overrides)
    except ValueError as exc:
        raise BadRequest(str(exc))

    return DatasetSummaryResponse(
        total_rows=summary.total_rows,
        total_columns=summary.total_columns,
        numeric_columns=summary.numeric_columns,
        categorical_columns=summary.categorical_columns,
        datetime_columns=summary.datetime_columns,
        boolean_columns=summary.boolean_columns,
        complete_rows=summary.complete_rows,
        duplicate_rows=summary.duplicate_rows,
        missing_cells=summary.missing_cells,
        missing_rate=summary.missing_rate,
        columns=[
            ColumnSummaryResponse(
                name=column.name,
                kind=column.kind,
                kind_source=column.kind_source,
                non_null_count=column.non_null_count,
                missing_count=column.missing_count,
                missing_rate=column.missing_rate,
                unique_count=column.unique_count,
                sample_values=column.sample_values,
                numeric_min=column.numeric_min,
                numeric_max=column.numeric_max,
                numeric_mean=column.numeric_mean,
                numeric_std=column.numeric_std,
                numeric_median=column.numeric_median,
                numeric_q1=column.numeric_q1,
                numeric_q3=column.numeric_q3,
                datetime_min=column.datetime_min,
                datetime_max=column.datetime_max,
                top_values=[
                    ValueFrequencyResponse(value=item.value, count=item.count, ratio=item.ratio)
                    for item in (column.top_values or [])
                ] or None,
            )
            for column in summary.columns
        ],
    )


@router.post("/{dataset_id}/clean", response_model=DatasetCleaningResultResponse)
async def clean_dataset(
    dataset_id: uuid.UUID,
    payload: DatasetCleaningRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """执行数据清洗并生成新的数据集副本。"""
    dataset = await _get_dataset_for_user(dataset_id, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()

    result = clean_dataset_content(
        content=content,
        ext=ext,
        original_name=dataset.name,
        payload=payload,
        type_overrides=await get_dataset_kind_overrides(db, str(dataset.id)),
    )

    cleaned_file_id = uuid.uuid4()
    object_key = f"{current_user.id}/{dataset.project_id}/{cleaned_file_id}.csv"
    await storage_service.upload(
        object_key=object_key,
        content=result.csv_content,
        content_type="text/csv",
    )

    cleaned_dataset = Dataset(
        project_id=dataset.project_id,
        name=result.file_name,
        file_path=object_key,
        file_size=len(result.csv_content),
        file_format="csv",
        row_count=result.cleaned_rows,
        column_count=result.cleaned_columns,
        uploaded_by=current_user.id,
    )

    try:
        db.add(cleaned_dataset)
        await db.flush()
    except Exception:
        await storage_service.delete(object_key)
        raise

    return DatasetCleaningResultResponse(
        dataset=DatasetResponse(
            id=str(cleaned_dataset.id),
            name=cleaned_dataset.name,
            file_size=cleaned_dataset.file_size,
            file_format=cleaned_dataset.file_format,
            row_count=cleaned_dataset.row_count,
            column_count=cleaned_dataset.column_count,
            created_at=cleaned_dataset.created_at,
        ),
        original_rows=result.original_rows,
        original_columns=result.original_columns,
        cleaned_rows=result.cleaned_rows,
        cleaned_columns=result.cleaned_columns,
        removed_rows=result.removed_rows,
        removed_columns=result.removed_columns,
        numeric_imputed_cells=result.numeric_imputed_cells,
        categorical_imputed_cells=result.categorical_imputed_cells,
        encoded_columns_added=result.encoded_columns_added,
        operations=result.operations,
    )


@router.put("/{dataset_id}/columns/{column_name}/kind", response_model=DatasetColumnKindUpdateResponse)
async def update_dataset_column_kind(
    dataset_id: uuid.UUID,
    column_name: str,
    payload: DatasetColumnKindUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a dataset column kind override for downstream statistics."""
    dataset = await _get_dataset_for_user(dataset_id, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    summary = summarize_tabular_content(content, ext)

    available_columns = {column.name for column in summary.columns}
    if column_name not in available_columns:
        raise NotFound("变量不存在")

    requested_kind = normalize_dataset_kind(payload.kind)
    base_column = next((column for column in summary.columns if column.name == column_name), None)
    if base_column and base_column.kind in {"datetime", "boolean"} and requested_kind != "auto":
        raise BadRequest("日期或布尔变量暂不支持手动改为连续/分类变量")

    normalized_kind = await update_dataset_kind_override(db, str(dataset.id), column_name, requested_kind)
    if normalized_kind == "auto":
        auto_kind = next((column.kind for column in summary.columns if column.name == column_name), "categorical")
        return DatasetColumnKindUpdateResponse(
            column_name=column_name,
            kind=auto_kind,
            kind_source="auto",
        )

    return DatasetColumnKindUpdateResponse(
        column_name=column_name,
        kind=normalized_kind,
        kind_source="manual",
    )


@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """下载数据集原始文件。"""
    dataset = await _get_dataset_for_user(dataset_id, current_user, db)
    content = await storage_service.download(dataset.file_path)
    file_name = dataset.name or f"{dataset.id}.{dataset.file_format or 'csv'}"
    media_type = "text/csv" if (dataset.file_format or "").lower() == "csv" else "application/octet-stream"
    encoded_file_name = quote(file_name)

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"
        },
    )


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除数据集"""
    dataset = await _get_dataset_for_user(dataset_id, current_user, db)

    await storage_service.delete(dataset.file_path)

    await db.delete(dataset)
    await db.flush()
    return {"success": True}
