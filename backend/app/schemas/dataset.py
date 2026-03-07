"""Dataset-related Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


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


class ValueFrequencyResponse(BaseModel):
    value: str
    count: int
    ratio: float


class ColumnSummaryResponse(BaseModel):
    name: str
    kind: str
    kind_source: str = "auto"
    non_null_count: int
    missing_count: int
    missing_rate: float
    unique_count: int
    sample_values: list[str]
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_mean: float | None = None
    numeric_std: float | None = None
    numeric_median: float | None = None
    numeric_q1: float | None = None
    numeric_q3: float | None = None
    datetime_min: str | None = None
    datetime_max: str | None = None
    top_values: list[ValueFrequencyResponse] | None = None


class DatasetSummaryResponse(BaseModel):
    total_rows: int
    total_columns: int
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    boolean_columns: int
    complete_rows: int
    duplicate_rows: int
    missing_cells: int
    missing_rate: float
    columns: list[ColumnSummaryResponse]


class DatasetCleaningRequest(BaseModel):
    outlier_strategy: str = "none"
    outlier_factor: float = Field(default=1.5, ge=0.5, le=5.0)
    outlier_columns: list[str] = Field(default_factory=list)
    drop_high_missing_columns: bool = True
    missing_column_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    missing_drop_columns: list[str] = Field(default_factory=list)
    numeric_missing_strategy: str = "median"
    numeric_missing_columns: list[str] = Field(default_factory=list)
    categorical_missing_strategy: str = "mode"
    categorical_missing_columns: list[str] = Field(default_factory=list)
    scaling_strategy: str = "none"
    scaling_columns: list[str] = Field(default_factory=list)
    categorical_encoding: str = "none"
    encoding_columns: list[str] = Field(default_factory=list)
    output_name: str | None = None


class DatasetCleaningResultResponse(BaseModel):
    dataset: DatasetResponse
    original_rows: int
    original_columns: int
    cleaned_rows: int
    cleaned_columns: int
    removed_rows: int
    removed_columns: int
    numeric_imputed_cells: int
    categorical_imputed_cells: int
    encoded_columns_added: int
    operations: list[str]


class DictionaryEntry(BaseModel):
    column_name: str
    column_label: str | None = None
    data_type: str | None = None
    description: str | None = None
    codebook: dict | None = None

    model_config = {"from_attributes": True}


class DatasetColumnKindUpdateRequest(BaseModel):
    kind: str = Field(pattern="^(auto|con|cat|continuous|categorical|numeric)$")


class DatasetColumnKindUpdateResponse(BaseModel):
    column_name: str
    kind: str
    kind_source: str
