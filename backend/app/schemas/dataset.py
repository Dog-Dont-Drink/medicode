"""Dataset-related Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: str
    name: str
    file_size: int | None = None
    file_format: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    total_columns: int


class DictionaryEntry(BaseModel):
    column_name: str
    column_label: str | None = None
    data_type: str | None = None
    description: str | None = None
    codebook: dict | None = None

    model_config = {"from_attributes": True}
