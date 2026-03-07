"""Service for generating Table 1 baseline tables with tableone."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, Side
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype
from scipy import stats
from tableone import TableOne

from app.core.exceptions import BadRequest
from app.services.r_runtime import run_rscript
from app.services.dataset_parser import infer_dataframe_column_kinds, load_tabular_dataframe


@dataclass
class TableOneExecutionResult:
    title: str
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    headers: list[str]
    rows: list[list[str]]
    continuous_variables: list[str]
    categorical_variables: list[str]
    nonnormal_variables: list[str]
    normality_method: str
    excel_content: bytes


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _is_continuous(series: pd.Series) -> bool:
    return is_numeric_dtype(series) and not is_bool_dtype(series) and not is_datetime64_any_dtype(series)


def _is_categorical(series: pd.Series) -> bool:
    return is_bool_dtype(series) or (not is_numeric_dtype(series) and not is_datetime64_any_dtype(series))


def _normality_method(values: pd.Series) -> tuple[bool, str]:
    non_null = values.dropna().astype(float)
    sample_size = int(non_null.shape[0])
    if sample_size < 3:
        return False, "样本量过小，按非正态处理"

    if sample_size <= 5000:
        _, p_value = stats.shapiro(non_null)
        return bool(p_value >= 0.05), "Shapiro-Wilk"

    _, p_value = stats.normaltest(non_null)
    return bool(p_value >= 0.05), "D'Agostino-Pearson"


def _sanitize_continuous_groups(*groups: object) -> list[np.ndarray]:
    cleaned_groups: list[np.ndarray] = []
    for group in groups:
        values = pd.Series(group).dropna().astype(float).to_numpy()
        if values.size == 0:
            return []
        cleaned_groups.append(values)
    return cleaned_groups


def _mann_whitney_u_test(*groups: object) -> float:
    cleaned_groups = _sanitize_continuous_groups(*groups)
    if len(cleaned_groups) != 2:
        return float("nan")
    _, p_value = stats.mannwhitneyu(cleaned_groups[0], cleaned_groups[1], alternative="two-sided")
    return float(p_value)


_mann_whitney_u_test.__name__ = "Mann-Whitney U"


def _kruskal_wallis_test(*groups: object) -> float:
    cleaned_groups = _sanitize_continuous_groups(*groups)
    if len(cleaned_groups) < 3:
        return float("nan")
    _, p_value = stats.kruskal(*cleaned_groups)
    return float(p_value)


_kruskal_wallis_test.__name__ = "Kruskal-Wallis"


def _build_contingency_table(*categories: object) -> np.ndarray:
    if not categories:
        return np.empty((0, 0), dtype=int)
    contingency_table = np.asarray(categories, dtype=float).T
    if contingency_table.ndim != 2 or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return np.empty((0, 0), dtype=int)
    return np.rint(contingency_table).astype(int)


def _r_fisher_exact_p_value(contingency_table: np.ndarray) -> float:
    flattened = ",".join(str(int(value)) for value in contingency_table.ravel())
    r_script = """
args <- commandArgs(trailingOnly = TRUE)
n_row <- as.integer(args[1])
n_col <- as.integer(args[2])
values <- as.numeric(strsplit(args[3], ",", fixed = TRUE)[[1]])
matrix_data <- matrix(values, nrow = n_row, byrow = TRUE)
test_result <- stats::fisher.test(matrix_data, workspace = 2e8)
cat(format(test_result$p.value, scientific = TRUE))
"""
    with tempfile.TemporaryDirectory(prefix="medicode-fisher-") as temp_dir:
        script_path = Path(temp_dir) / "fisher_exact.R"
        script_path.write_text(r_script, encoding="utf-8")
        completed = run_rscript(
            [str(script_path), str(contingency_table.shape[0]), str(contingency_table.shape[1]), flattened],
            "R fisher.test 执行失败，无法完成 RxC 精确检验",
        )

    output = completed.stdout.strip()
    if not output:
        raise BadRequest("R fisher.test 未返回有效结果")

    try:
        return float(output)
    except ValueError as exc:
        raise BadRequest("R fisher.test 返回结果无法解析") from exc


def _build_hypothesis_tests(
    categorical_variables: list[str],
    nonnormal_variables: list[str],
    group_count: int,
) -> dict[str, object]:
    hypothesis_tests: dict[str, object] = {}

    def categorical_exact_or_chi_square_test(*categories: object) -> float:
        contingency_table = _build_contingency_table(*categories)
        if contingency_table.size == 0:
            categorical_exact_or_chi_square_test.__name__ = "Not tested"
            return float("nan")
        if np.any(contingency_table.sum(axis=0) == 0) or np.any(contingency_table.sum(axis=1) == 0):
            categorical_exact_or_chi_square_test.__name__ = "Not tested"
            return float("nan")

        _, p_value, _, expected = stats.chi2_contingency(contingency_table)
        if np.any(expected < 5):
            categorical_exact_or_chi_square_test.__name__ = "Fisher's exact"
            if contingency_table.shape == (2, 2):
                _, fisher_p_value = stats.fisher_exact(contingency_table)
                return float(fisher_p_value)
            return _r_fisher_exact_p_value(contingency_table)

        categorical_exact_or_chi_square_test.__name__ = "Chi-squared"
        return float(p_value)

    categorical_exact_or_chi_square_test.__name__ = "Chi-squared"

    for column in categorical_variables:
        hypothesis_tests[column] = categorical_exact_or_chi_square_test

    for column in nonnormal_variables:
        hypothesis_tests[column] = _mann_whitney_u_test if group_count == 2 else _kruskal_wallis_test

    return hypothesis_tests


def _flatten_table(table_df: pd.DataFrame) -> tuple[list[str], list[list[str]], pd.DataFrame]:
    flattened = table_df.reset_index()
    headers: list[str] = []
    for column in flattened.columns:
        if isinstance(column, tuple):
            first, second = column
            if first == "level_0":
                headers.append("变量")
            elif first == "level_1":
                headers.append("水平")
            else:
                headers.append(str(second or first))
        else:
            headers.append(str(column))

    rows: list[list[str]] = []
    for _, row in flattened.iterrows():
        rendered_row: list[str] = []
        for value in row.tolist():
            if pd.isna(value):
                rendered_row.append("")
            else:
                rendered_row.append(str(value))
        rows.append(rendered_row)

    export_df = pd.DataFrame(rows, columns=headers)
    return headers, rows, export_df


def _render_excel(export_df: pd.DataFrame, sheet_name: str = "Table1") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]

        top_side = Side(style="thin", color="000000")
        header_font = Font(bold=True)

        for cell in worksheet[1]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(top=top_side, bottom=top_side)

        last_row = worksheet.max_row
        for cell in worksheet[last_row]:
            cell.border = Border(bottom=top_side)

        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 4, 32)

    buffer.seek(0)
    return buffer.read()


def generate_tableone(
    content: bytes,
    ext: str,
    dataset_name: str,
    group_variable: str,
    variables: list[str],
    decimals: int = 1,
    type_overrides: dict[str, str] | None = None,
) -> TableOneExecutionResult:
    df = load_tabular_dataframe(content, ext)
    if group_variable not in df.columns:
        raise BadRequest("分组变量不存在")

    selected_variables = _deduplicate(variables)
    if not selected_variables:
        raise BadRequest("请至少选择一个统计变量")
    if group_variable in selected_variables:
        raise BadRequest("分组变量不应重复放入统计变量中")

    invalid_columns = [column for column in selected_variables if column not in df.columns]
    if invalid_columns:
        raise BadRequest(f"存在无效统计变量: {', '.join(invalid_columns[:5])}")

    group_series = df[group_variable].dropna()
    group_levels = group_series.astype(str).unique().tolist()
    if len(group_levels) < 2 or len(group_levels) > 4:
        raise BadRequest("分组变量只支持 2 到 4 个组别")

    kind_map = infer_dataframe_column_kinds(df, type_overrides)
    continuous_variables = [column for column in selected_variables if kind_map.get(column, ("categorical", "auto"))[0] == "numeric"]
    categorical_variables = [column for column in selected_variables if kind_map.get(column, ("categorical", "auto"))[0] in {"categorical", "boolean"}]
    unsupported_variables = [
        column for column in selected_variables
        if column not in continuous_variables and column not in categorical_variables
    ]
    if unsupported_variables:
        raise BadRequest(f"以下变量暂不支持 Table 1 统计: {', '.join(unsupported_variables[:5])}")

    high_cardinality_categorical: list[str] = []
    for column in categorical_variables:
        non_null_count = int(df[column].notna().sum())
        unique_count = int(df[column].dropna().astype(str).nunique())
        if unique_count > 20 or (non_null_count >= 10 and unique_count / max(non_null_count, 1) >= 0.5):
            high_cardinality_categorical.append(column)
    if high_cardinality_categorical:
        raise BadRequest(
            "以下分类变量水平过多或接近唯一值，不适合基线统计，请去掉 ID 类字段后重试: "
            + ", ".join(high_cardinality_categorical[:5])
        )

    nonnormal_variables: list[str] = []
    normality_method = "Shapiro-Wilk（n<=5000）/ D'Agostino-Pearson（n>5000）"
    for column in continuous_variables:
        is_normal, _ = _normality_method(df[column])
        if not is_normal:
            nonnormal_variables.append(column)

    analysis_df = df[[group_variable, *selected_variables]].copy()
    for column in continuous_variables:
        analysis_df[column] = pd.to_numeric(analysis_df[column], errors="coerce")
    for column in categorical_variables:
        analysis_df[column] = analysis_df[column].astype("string")
    hypothesis_tests = _build_hypothesis_tests(
        categorical_variables=categorical_variables,
        nonnormal_variables=nonnormal_variables,
        group_count=len(group_levels),
    )
    table = TableOne(
        analysis_df,
        columns=selected_variables,
        categorical=categorical_variables,
        continuous=continuous_variables,
        groupby=group_variable,
        nonnormal=nonnormal_variables,
        htest=hypothesis_tests,
        pval=True,
        htest_name=True,
        missing=True,
        overall=True,
        label_suffix=True,
        decimals=decimals,
        include_null=False,
        pval_digits=3,
        ttest_equal_var=False,
    )

    headers, rows, export_df = _flatten_table(table.tableone)
    excel_content = _render_excel(export_df)
    title = f"Table 1. Baseline characteristics by {group_variable}"

    return TableOneExecutionResult(
        title=title,
        dataset_name=dataset_name,
        group_variable=group_variable,
        group_levels=group_levels,
        headers=headers,
        rows=rows,
        continuous_variables=continuous_variables,
        categorical_variables=categorical_variables,
        nonnormal_variables=nonnormal_variables,
        normality_method=normality_method,
        excel_content=excel_content,
    )
