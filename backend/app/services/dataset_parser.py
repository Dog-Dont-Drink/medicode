"""Parse tabular datasets (CSV/Excel) for validation, profiling and preview."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from math import isnan
from typing import Any

import pandas as pd
import numpy as np
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
CSV_ENCODINGS = ("utf-8", "utf-8-sig", "gbk", "gb2312", "latin1")


@dataclass
class ParsedDataset:
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    total_columns: int


@dataclass
class ValueFrequency:
    value: str
    count: int
    ratio: float


@dataclass
class ColumnSummary:
    name: str
    kind: str
    kind_source: str
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
    top_values: list[ValueFrequency] | None = None


@dataclass
class DatasetSummary:
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
    columns: list[ColumnSummary]


def _to_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and isnan(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if pd.isna(value):
        return None
    return value


def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in records:
        normalized.append({str(key): _to_json_value(value) for key, value in row.items()})
    return normalized


def _read_csv(content: bytes) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(BytesIO(content), encoding=encoding, low_memory=False)
        except UnicodeDecodeError as exc:
            last_error = exc
        except Exception as exc:  # malformed CSV, delimiter issues, etc.
            last_error = exc
            break

    raise ValueError("CSV 文件读取失败，请确认编码与格式正确。") from last_error


def _read_excel(content: bytes, ext: str) -> pd.DataFrame:
    engine = "openpyxl" if ext == ".xlsx" else "xlrd"
    try:
        return pd.read_excel(BytesIO(content), engine=engine)
    except Exception as exc:
        raise ValueError("Excel 文件读取失败，请确认文件未损坏。") from exc


def load_tabular_dataframe(content: bytes, ext: str) -> pd.DataFrame:
    normalized_ext = ext.lower().strip()
    if normalized_ext not in SUPPORTED_EXTENSIONS:
        raise ValueError("仅支持 CSV、XLSX、XLS 文件。")

    if normalized_ext == ".csv":
        return _read_csv(content)
    return _read_excel(content, normalized_ext)


def _round_number(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def _format_display_value(value: Any) -> str:
    normalized = _to_json_value(value)
    if normalized is None:
        return "-"
    return str(normalized)


def _coerce_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _looks_like_discrete_numeric(series: pd.Series) -> bool:
    non_null = _coerce_numeric_series(series).dropna()
    if non_null.empty:
        return False
    unique_count = int(non_null.nunique(dropna=True))
    if unique_count < 2 or unique_count > 6:
        return False
    return bool(np.isclose(non_null % 1, 0).all())


def _infer_column_kind(series: pd.Series, override_kind: str | None = None) -> tuple[str, str]:
    if override_kind in {"numeric", "categorical", "datetime", "boolean"}:
        return override_kind, "manual"
    if is_bool_dtype(series):
        return "boolean", "auto"
    if is_datetime64_any_dtype(series):
        return "datetime", "auto"
    if is_numeric_dtype(series):
        if _looks_like_discrete_numeric(series):
            return "categorical", "auto"
        return "numeric", "auto"
    return "categorical", "auto"


def infer_dataframe_column_kinds(
    df: pd.DataFrame,
    kind_overrides: dict[str, str] | None = None,
) -> dict[str, tuple[str, str]]:
    overrides = kind_overrides or {}
    return {
        str(column_name): _infer_column_kind(df[column_name], overrides.get(str(column_name)))
        for column_name in df.columns.tolist()
    }


def summarize_tabular_content(
    content: bytes,
    ext: str,
    kind_overrides: dict[str, str] | None = None,
) -> DatasetSummary:
    if not content:
        raise ValueError("上传文件为空，请选择有效的数据文件。")

    df = load_tabular_dataframe(content, ext)
    total_rows = int(df.shape[0])
    total_columns = int(df.shape[1])
    missing_cells = int(df.isna().sum().sum())
    total_cells = total_rows * total_columns
    missing_rate = round((missing_cells / total_cells), 4) if total_cells else 0.0

    column_summaries: list[ColumnSummary] = []
    numeric_columns = 0
    categorical_columns = 0
    datetime_columns = 0
    boolean_columns = 0

    resolved_kinds = infer_dataframe_column_kinds(df, kind_overrides)

    for column_name in df.columns.tolist():
        series = df[column_name]
        non_null = series.dropna()
        non_null_count = int(non_null.shape[0])
        missing_count = int(series.isna().sum())
        unique_count = int(non_null.nunique(dropna=True))
        missing_ratio = round((missing_count / total_rows), 4) if total_rows else 0.0
        sample_values = [_format_display_value(value) for value in non_null.head(3).tolist()]
        kind, kind_source = resolved_kinds[str(column_name)]
        numeric_series = _coerce_numeric_series(series) if kind == "numeric" else series
        non_null_numeric = numeric_series.dropna() if kind == "numeric" else None

        top_values: list[ValueFrequency] | None = None
        numeric_min = numeric_max = numeric_mean = numeric_std = numeric_median = None
        numeric_q1 = numeric_q3 = None
        datetime_min = datetime_max = None

        if kind == "numeric":
            numeric_columns += 1
            numeric_min = _round_number(non_null_numeric.min()) if non_null_count else None
            numeric_max = _round_number(non_null_numeric.max()) if non_null_count else None
            numeric_mean = _round_number(non_null_numeric.mean()) if non_null_count else None
            numeric_std = _round_number(non_null_numeric.std()) if non_null_count else None
            numeric_median = _round_number(non_null_numeric.median()) if non_null_count else None
            numeric_q1 = _round_number(non_null_numeric.quantile(0.25)) if non_null_count else None
            numeric_q3 = _round_number(non_null_numeric.quantile(0.75)) if non_null_count else None
        elif kind == "datetime":
            datetime_columns += 1
            if non_null_count:
                datetime_min = _format_display_value(non_null.min())
                datetime_max = _format_display_value(non_null.max())
        else:
            if kind == "boolean":
                boolean_columns += 1
            else:
                categorical_columns += 1
            if non_null_count:
                value_counts = non_null.astype(str).value_counts(dropna=True).head(4)
                top_values = [
                    ValueFrequency(
                        value=str(value),
                        count=int(count),
                        ratio=round((int(count) / non_null_count), 4),
                    )
                    for value, count in value_counts.items()
                ]

        column_summaries.append(
            ColumnSummary(
                name=str(column_name),
                kind=kind,
                kind_source=kind_source,
                non_null_count=non_null_count,
                missing_count=missing_count,
                missing_rate=missing_ratio,
                unique_count=unique_count,
                sample_values=sample_values,
                numeric_min=numeric_min,
                numeric_max=numeric_max,
                numeric_mean=numeric_mean,
                numeric_std=numeric_std,
                numeric_median=numeric_median,
                numeric_q1=numeric_q1,
                numeric_q3=numeric_q3,
                datetime_min=datetime_min,
                datetime_max=datetime_max,
                top_values=top_values,
            )
        )

    return DatasetSummary(
        total_rows=total_rows,
        total_columns=total_columns,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        datetime_columns=datetime_columns,
        boolean_columns=boolean_columns,
        complete_rows=int(df.dropna().shape[0]),
        duplicate_rows=int(df.duplicated().sum()),
        missing_cells=missing_cells,
        missing_rate=missing_rate,
        columns=column_summaries,
    )


def parse_tabular_content(
    content: bytes,
    ext: str,
    preview_rows: int = 5,
    max_rows: int | None = None,
) -> ParsedDataset:
    if not content:
        raise ValueError("上传文件为空，请选择有效的数据文件。")

    normalized_ext = ext.lower().strip()
    df = load_tabular_dataframe(content, normalized_ext)

    total_rows = int(df.shape[0])
    if max_rows is not None and total_rows > max_rows:
        raise ValueError(f"免费版最多支持 {max_rows} 行数据，请升级付费套餐后上传更大数据集。")

    columns = [str(col) for col in df.columns.tolist()]
    records = df.head(preview_rows).to_dict(orient="records")

    return ParsedDataset(
        columns=columns,
        rows=_normalize_records(records),
        total_rows=total_rows,
        total_columns=int(df.shape[1]),
    )


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output.getvalue()
