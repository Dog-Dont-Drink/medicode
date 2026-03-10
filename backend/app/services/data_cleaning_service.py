"""Dataset cleaning service for common preprocessing operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

from app.core.exceptions import BadRequest
from app.schemas.dataset import DatasetCleaningRequest
from app.services.dataset_parser import dataframe_to_csv_bytes, infer_dataframe_column_kinds, load_tabular_dataframe


OUTLIER_STRATEGIES = {"none", "clip_iqr", "remove_rows"}
NUMERIC_MISSING_STRATEGIES = {"none", "mean", "median", "multiple_imputation"}
CATEGORICAL_MISSING_STRATEGIES = {"none", "mode", "unknown"}
SCALING_STRATEGIES = {"none", "normalize", "standardize", "center"}
CATEGORICAL_ENCODINGS = {"none", "one_hot"}


@dataclass
class CleaningExecutionResult:
    csv_content: bytes
    file_name: str
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


def _validate_request(payload: DatasetCleaningRequest) -> None:
    if payload.outlier_strategy not in OUTLIER_STRATEGIES:
        raise BadRequest("不支持的极端值处理方式")
    if payload.numeric_missing_strategy not in NUMERIC_MISSING_STRATEGIES:
        raise BadRequest("不支持的数值缺失值处理方式")
    if payload.categorical_missing_strategy not in CATEGORICAL_MISSING_STRATEGIES:
        raise BadRequest("不支持的分类缺失值处理方式")
    if payload.scaling_strategy not in SCALING_STRATEGIES:
        raise BadRequest("不支持的数值缩放方式")
    if payload.categorical_encoding not in CATEGORICAL_ENCODINGS:
        raise BadRequest("不支持的分类变量编码方式")


def _deduplicate_columns(columns: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for column in columns:
        value = str(column).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def _validate_selected_columns(
    requested: list[str],
    available: list[str],
    label: str,
) -> list[str]:
    normalized = _deduplicate_columns(requested)
    if not normalized:
        return []

    invalid = [column for column in normalized if column not in available]
    if invalid:
        raise BadRequest(f"{label}包含无效或类型不匹配的变量: {', '.join(invalid[:5])}")
    return normalized


def _resolve_runtime_columns(df: pd.DataFrame, requested: list[str], fallback: list[str]) -> list[str]:
    current_columns = {str(column) for column in df.columns}
    if requested:
        return [column for column in requested if column in current_columns]
    return [column for column in fallback if column in current_columns]


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [
        str(column)
        for column in df.columns
        if is_numeric_dtype(df[column]) and not is_bool_dtype(df[column])
    ]


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    columns: list[str] = []
    for column in df.columns:
        series = df[column]
        if is_datetime64_any_dtype(series) or is_numeric_dtype(series):
            continue
        columns.append(str(column))
    return columns


def _datetime_columns(df: pd.DataFrame) -> list[str]:
    return [str(column) for column in df.columns if is_datetime64_any_dtype(df[column])]


def _drop_high_missing_columns(
    df: pd.DataFrame,
    threshold: float,
    target_columns: list[str],
    operations: list[str],
) -> tuple[pd.DataFrame, int]:
    if df.empty:
        return df, 0

    if not target_columns:
        return df, 0

    missing_rates = df[target_columns].isna().mean()
    to_drop = [str(column) for column, rate in missing_rates.items() if float(rate) > threshold]
    if not to_drop:
        return df, 0

    scope_text = "所选变量" if len(target_columns) != len(df.columns) else "变量"
    operations.append(f"剔除缺失比例超过 {threshold * 100:.0f}% 的{scope_text} {len(to_drop)} 个")
    return df.drop(columns=to_drop), len(to_drop)


def _handle_outliers(
    df: pd.DataFrame,
    strategy: str,
    factor: float,
    target_columns: list[str],
    operations: list[str],
) -> tuple[pd.DataFrame, int]:
    numeric_columns = target_columns
    if strategy == "none" or not numeric_columns:
        return df, 0

    if strategy == "clip_iqr":
        clipped_columns = 0
        next_df = df.copy()
        for column in numeric_columns:
            series = next_df[column]
            non_null = series.dropna()
            if non_null.empty:
                continue
            q1 = non_null.quantile(0.25)
            q3 = non_null.quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or float(iqr) == 0:
                continue
            lower = q1 - factor * iqr
            upper = q3 + factor * iqr
            next_df[column] = series.clip(lower=lower, upper=upper)
            clipped_columns += 1

        if clipped_columns:
            operations.append(f"使用 IQR 截尾处理 {clipped_columns} 个指定连续变量的极端值")
        return next_df, 0

    mask = pd.Series(False, index=df.index)
    for column in numeric_columns:
        series = df[column]
        non_null = series.dropna()
        if non_null.empty:
            continue
        q1 = non_null.quantile(0.25)
        q3 = non_null.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or float(iqr) == 0:
            continue
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        mask = mask | ((series < lower) | (series > upper)).fillna(False)

    removed_rows = int(mask.sum())
    if removed_rows:
        operations.append(f"依据 IQR 规则删除 {removed_rows} 行指定连续变量含极端值观测")
    return df.loc[~mask].reset_index(drop=True), removed_rows


def _multiple_impute_numeric(series: pd.Series) -> pd.Series:
    non_null = series.dropna()
    if non_null.empty:
        return series
    mu = non_null.mean()
    sigma = non_null.std(ddof=1)
    if pd.isna(sigma) or sigma == 0:
        return series.fillna(mu)
    rng = np.random.default_rng(seed=42)
    mask = series.isna()
    imputed_values = rng.normal(loc=mu, scale=sigma, size=int(mask.sum()))
    result = series.copy()
    result.loc[mask] = imputed_values
    return result


def _fill_numeric_missing(
    df: pd.DataFrame,
    strategy: str,
    target_columns: list[str],
    operations: list[str],
) -> tuple[pd.DataFrame, int]:
    numeric_columns = target_columns
    if strategy == "none" or not numeric_columns:
        return df, 0

    next_df = df.copy()
    missing_cells = int(next_df[numeric_columns].isna().sum().sum())
    if missing_cells == 0:
        return next_df, 0

    for column in numeric_columns:
        series = next_df[column]
        if not series.isna().any():
            continue
        if strategy == "mean":
            value = series.dropna().mean()
            next_df[column] = series.fillna(value)
        elif strategy == "median":
            value = series.dropna().median()
            next_df[column] = series.fillna(value)
        elif strategy == "multiple_imputation":
            next_df[column] = _multiple_impute_numeric(series)

    labels = {
        "mean": "均值填补",
        "median": "中位数填补",
        "multiple_imputation": "简化多重插补",
    }
    operations.append(f"对 {missing_cells} 个指定数值缺失单元执行{labels[strategy]}")
    return next_df, missing_cells


def _fill_categorical_missing(
    df: pd.DataFrame,
    strategy: str,
    target_columns: list[str],
    operations: list[str],
) -> tuple[pd.DataFrame, int]:
    categorical_columns = target_columns
    if strategy == "none" or not categorical_columns:
        return df, 0

    next_df = df.copy()
    missing_cells = int(next_df[categorical_columns].isna().sum().sum())
    if missing_cells == 0:
        return next_df, 0

    for column in categorical_columns:
        series = next_df[column]
        if not series.isna().any():
            continue
        if strategy == "mode":
            mode = series.mode(dropna=True)
            fill_value = mode.iloc[0] if not mode.empty else "Unknown"
        else:
            fill_value = "Unknown"
        next_df[column] = series.fillna(fill_value)

    labels = {
        "mode": "众数填补",
        "unknown": "Unknown 填补",
    }
    operations.append(f"对 {missing_cells} 个指定分类缺失单元执行{labels[strategy]}")
    return next_df, missing_cells


def _scale_numeric(
    df: pd.DataFrame,
    strategy: str,
    target_columns: list[str],
    operations: list[str],
) -> pd.DataFrame:
    numeric_columns = target_columns
    if strategy == "none" or not numeric_columns:
        return df

    next_df = df.copy()
    for column in numeric_columns:
        series = next_df[column].astype(float)
        if strategy == "normalize":
            min_value = series.min()
            max_value = series.max()
            if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
                continue
            next_df[column] = (series - min_value) / (max_value - min_value)
        elif strategy == "standardize":
            std = series.std()
            if pd.isna(std) or std == 0:
                continue
            next_df[column] = (series - series.mean()) / std
        else:
            next_df[column] = series - series.mean()

    labels = {
        "normalize": "Min-Max 归一化",
        "standardize": "Z-score 标准化",
        "center": "均值中心化",
    }
    operations.append(f"对 {len(numeric_columns)} 个指定连续变量执行{labels[strategy]}")
    return next_df


def _encode_categorical(
    df: pd.DataFrame,
    strategy: str,
    target_columns: list[str],
    operations: list[str],
) -> tuple[pd.DataFrame, int]:
    categorical_columns = target_columns
    if strategy == "none" or not categorical_columns:
        return df, 0

    next_df = pd.get_dummies(
        df,
        columns=categorical_columns,
        prefix=categorical_columns,
        dummy_na=False,
        dtype=int,
    )
    added_columns = int(next_df.shape[1] - df.shape[1])
    operations.append(f"对 {len(categorical_columns)} 个指定分类变量执行哑变量编码，新增 {added_columns} 列")
    return next_df, added_columns


def clean_dataset_content(
    content: bytes,
    ext: str,
    original_name: str,
    payload: DatasetCleaningRequest,
    type_overrides: dict[str, str] | None = None,
) -> CleaningExecutionResult:
    _validate_request(payload)

    df = load_tabular_dataframe(content, ext)
    operations: list[str] = []
    original_rows = int(df.shape[0])
    original_columns = int(df.shape[1])
    all_columns = [str(column) for column in df.columns]
    kind_map = infer_dataframe_column_kinds(df, type_overrides)
    numeric_columns = [column for column, (kind, _) in kind_map.items() if kind == "numeric"]
    categorical_columns = [column for column, (kind, _) in kind_map.items() if kind in {"categorical", "boolean"}]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    selected_outlier_columns = _validate_selected_columns(payload.outlier_columns, numeric_columns, "极端值处理变量")
    selected_missing_drop_columns = _validate_selected_columns(payload.missing_drop_columns, all_columns, "高缺失变量剔除范围")
    selected_numeric_missing_columns = _validate_selected_columns(payload.numeric_missing_columns, numeric_columns, "数值缺失值处理变量")
    selected_categorical_missing_columns = _validate_selected_columns(payload.categorical_missing_columns, categorical_columns, "分类缺失值处理变量")
    selected_scaling_columns = _validate_selected_columns(payload.scaling_columns, numeric_columns, "数值变换变量")
    selected_encoding_columns = _validate_selected_columns(payload.encoding_columns, categorical_columns, "分类编码变量")

    next_df = df.copy()
    removed_columns = 0
    removed_rows = 0
    numeric_imputed_cells = 0
    categorical_imputed_cells = 0
    encoded_columns_added = 0

    if payload.drop_high_missing_columns:
        drop_columns = _resolve_runtime_columns(next_df, selected_missing_drop_columns, all_columns)
        next_df, removed_columns = _drop_high_missing_columns(
            next_df,
            payload.missing_column_threshold,
            drop_columns,
            operations,
        )

    outlier_columns = _resolve_runtime_columns(next_df, selected_outlier_columns, numeric_columns)
    next_df, removed_rows = _handle_outliers(
        next_df,
        payload.outlier_strategy,
        payload.outlier_factor,
        outlier_columns,
        operations,
    )

    numeric_missing_columns = _resolve_runtime_columns(next_df, selected_numeric_missing_columns, numeric_columns)
    next_df, numeric_imputed_cells = _fill_numeric_missing(
        next_df,
        payload.numeric_missing_strategy,
        numeric_missing_columns,
        operations,
    )

    categorical_missing_columns_resolved = _resolve_runtime_columns(next_df, selected_categorical_missing_columns, categorical_columns)
    next_df, categorical_imputed_cells = _fill_categorical_missing(
        next_df,
        payload.categorical_missing_strategy,
        categorical_missing_columns_resolved,
        operations,
    )

    scaling_columns = _resolve_runtime_columns(next_df, selected_scaling_columns, numeric_columns)
    next_df = _scale_numeric(
        next_df,
        payload.scaling_strategy,
        scaling_columns,
        operations,
    )

    encoding_columns = _resolve_runtime_columns(next_df, selected_encoding_columns, categorical_columns)
    next_df, encoded_columns_added = _encode_categorical(
        next_df,
        payload.categorical_encoding,
        encoding_columns,
        operations,
    )

    cleaned_rows = int(next_df.shape[0])
    cleaned_columns = int(next_df.shape[1])
    output_name = payload.output_name or f"{Path(original_name).stem}_cleaned.csv"
    if not output_name.lower().endswith(".csv"):
        output_name = f"{output_name}.csv"

    if not operations:
        operations.append("未选择额外清洗策略，已生成结构化副本")

    return CleaningExecutionResult(
        csv_content=dataframe_to_csv_bytes(next_df),
        file_name=output_name,
        original_rows=original_rows,
        original_columns=original_columns,
        cleaned_rows=cleaned_rows,
        cleaned_columns=cleaned_columns,
        removed_rows=removed_rows,
        removed_columns=removed_columns,
        numeric_imputed_cells=numeric_imputed_cells,
        categorical_imputed_cells=categorical_imputed_cells,
        encoded_columns_added=encoded_columns_added,
        operations=operations,
    )
