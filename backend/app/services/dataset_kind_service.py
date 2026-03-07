"""Dataset column kind overrides and normalization helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest
from app.db.models.dataset import DatasetDictionary

NORMALIZED_KIND_MAP = {
    "auto": "auto",
    "con": "numeric",
    "continuous": "numeric",
    "numeric": "numeric",
    "cat": "categorical",
    "categorical": "categorical",
}
EDITABLE_KINDS = {"numeric", "categorical"}


def normalize_dataset_kind(kind: str) -> str:
    normalized = NORMALIZED_KIND_MAP.get(str(kind).strip().lower())
    if not normalized:
        raise BadRequest("类型仅支持 auto、con、cat、continuous、categorical")
    return normalized


async def get_dataset_kind_overrides(db: AsyncSession, dataset_id: str) -> dict[str, str]:
    result = await db.execute(
        select(DatasetDictionary.column_name, DatasetDictionary.data_type).where(
            DatasetDictionary.dataset_id == dataset_id,
            DatasetDictionary.data_type.is_not(None),
        )
    )

    overrides: dict[str, str] = {}
    for column_name, data_type in result.all():
        if not data_type:
            continue
        normalized = NORMALIZED_KIND_MAP.get(str(data_type).strip().lower())
        if normalized in EDITABLE_KINDS:
            overrides[str(column_name)] = normalized
    return overrides


async def update_dataset_kind_override(
    db: AsyncSession,
    dataset_id: str,
    column_name: str,
    kind: str,
) -> str:
    normalized = normalize_dataset_kind(kind)
    result = await db.execute(
        select(DatasetDictionary).where(
            DatasetDictionary.dataset_id == dataset_id,
            DatasetDictionary.column_name == column_name,
        )
    )
    entry = result.scalar_one_or_none()

    if normalized == "auto":
        if entry:
            entry.data_type = None
        return normalized

    if entry:
        entry.data_type = normalized
    else:
        db.add(
            DatasetDictionary(
                dataset_id=dataset_id,
                column_name=column_name,
                data_type=normalized,
            )
        )
    return normalized
