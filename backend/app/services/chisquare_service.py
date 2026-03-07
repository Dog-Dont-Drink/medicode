"""Service for running chi-squared and Fisher exact tests via R."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile

import pandas as pd

from app.core.exceptions import BadRequest


@dataclass
class ChiSquareLevelRowResult:
    level: str
    group_values: list[str]


@dataclass
class ChiSquareVariableResultData:
    variable: str
    level_rows: list[ChiSquareLevelRowResult]
    minimum_expected_count: float | None
    expected_count_warning: bool
    recommended_test: str
    executed_test: str
    statistic: float | None
    df: float | None
    p_value: float | None
    note: str


@dataclass
class ChiSquareExecutionResult:
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    alpha: float
    confirm_independence: bool
    assumptions: list[str]
    variables: list[ChiSquareVariableResultData]


def _round_nullable(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def run_chisquare(
    df: pd.DataFrame,
    dataset_name: str,
    group_variable: str,
    categorical_variables: list[str],
    alpha: float,
    confirm_independence: bool,
) -> ChiSquareExecutionResult:
    if group_variable not in df.columns:
        raise BadRequest("分组变量不存在")
    if not categorical_variables:
        raise BadRequest("请至少选择一个分类变量")
    analysis_df = df[[group_variable, *categorical_variables]].copy()
    analysis_df = analysis_df.dropna(subset=[group_variable])
    group_levels = analysis_df[group_variable].astype(str).dropna().unique().tolist()
    if len(group_levels) < 2 or len(group_levels) > 4:
        raise BadRequest("卡方检验仅支持 2 到 4 组的分组变量")

    invalid_columns = [column for column in categorical_variables if column not in analysis_df.columns]
    if invalid_columns:
        raise BadRequest(f"存在无效分类变量: {', '.join(invalid_columns[:5])}")

    for column in categorical_variables:
        analysis_df[column] = analysis_df[column].astype("string")

    with tempfile.TemporaryDirectory(prefix="medicode-chisquare-") as temp_dir:
        temp_path = Path(temp_dir)
        input_csv = temp_path / "input.csv"
        summary_csv = temp_path / "summary.csv"
        groups_csv = temp_path / "groups.csv"
        levels_csv = temp_path / "levels.csv"

        analysis_df.to_csv(input_csv, index=False, encoding="utf-8-sig")
        r_script = """
args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
summary_csv <- args[2]
groups_csv <- args[3]
levels_csv <- args[4]
group_var <- args[5]
variables <- strsplit(args[6], "\\t", fixed = FALSE)[[1]]

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE)
df[[group_var]] <- as.factor(df[[group_var]])
group_levels <- levels(droplevels(df[[group_var]]))

write.csv(data.frame(group = group_levels), groups_csv, row.names = FALSE)

summary_rows <- list()
level_rows <- list()
index <- 1

for (var_name in variables) {
  sub_df <- df[, c(group_var, var_name)]
  names(sub_df) <- c("group", "value")
  sub_df$group[sub_df$group %in% c("", "<NA>", "NA", "nan", "NaN")] <- NA
  sub_df$value[sub_df$value %in% c("", "<NA>", "NA", "nan", "NaN")] <- NA
  sub_df <- sub_df[complete.cases(sub_df), ]
  sub_df$group <- droplevels(as.factor(sub_df$group))
  sub_df$value <- droplevels(as.factor(sub_df$value))
  if (nlevels(sub_df$group) < 2 || nlevels(sub_df$value) < 2) {
    next
  }

  contingency <- table(sub_df$value, sub_df$group)
  chisq_result <- suppressWarnings(chisq.test(contingency, correct = FALSE))
  min_expected <- min(chisq_result$expected)
  expected_warning <- is.finite(min_expected) && min_expected < 5

  if (expected_warning) {
    test_result <- fisher.test(contingency, workspace = 2e8)
    executed_test <- "Fisher's exact"
    recommended_test <- "Fisher's exact"
    statistic <- NA
    df_value <- NA
    note <- "存在期望频数 < 5 的单元格，已自动改用 Fisher 精确概率法。"
  } else {
    test_result <- chisq_result
    executed_test <- "Chi-squared"
    recommended_test <- "Chi-squared"
    statistic <- unname(test_result$statistic)
    df_value <- unname(test_result$parameter)
    note <- "各单元格期望频数满足卡方检验要求，采用 Pearson 卡方检验。"
  }

  row_totals <- rowSums(contingency)
  for (i in seq_len(nrow(contingency))) {
    level_name <- rownames(contingency)[i]
    for (j in seq_len(ncol(contingency))) {
      group_name <- colnames(contingency)[j]
      count_value <- contingency[i, j]
      denominator <- row_totals[i]
      ratio <- if (denominator > 0) (count_value / denominator) * 100 else NA
      display_value <- if (is.na(ratio)) {
        paste0(count_value, " (NA)")
      } else {
        paste0(count_value, " (", sprintf("%.1f", ratio), "%)")
      }
      level_rows[[length(level_rows) + 1]] <- data.frame(
        variable = var_name,
        level = level_name,
        group = group_name,
        display_value = display_value
      )
    }
  }

  summary_rows[[index]] <- data.frame(
    variable = var_name,
    minimum_expected_count = min_expected,
    expected_count_warning = expected_warning,
    recommended_test = recommended_test,
    executed_test = executed_test,
    statistic = statistic,
    df = df_value,
    p_value = test_result$p.value,
    note = note
  )
  index <- index + 1
}

summary_df <- if (length(summary_rows)) do.call(rbind, summary_rows) else data.frame()
level_df <- if (length(level_rows)) do.call(rbind, level_rows) else data.frame()
write.csv(summary_df, summary_csv, row.names = FALSE)
write.csv(level_df, levels_csv, row.names = FALSE)
"""
        try:
            subprocess.run(
                [
                    "Rscript",
                    "-e",
                    r_script,
                    str(input_csv),
                    str(summary_csv),
                    str(groups_csv),
                    str(levels_csv),
                    group_variable,
                    "\t".join(categorical_variables),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise BadRequest("R 卡方检验执行失败，请确认本机已安装 Rscript 且数据格式正确") from exc

        if not summary_csv.exists():
            raise BadRequest("R 卡方检验未返回结果")

        summary_df = pd.read_csv(summary_csv)
        if summary_df.empty:
            raise BadRequest("没有可用于卡方检验的有效分类变量，请检查缺失值和变量类型")

        groups_df = pd.read_csv(groups_csv) if groups_csv.exists() else pd.DataFrame(columns=["group"])
        levels_df = pd.read_csv(levels_csv) if levels_csv.exists() and levels_csv.stat().st_size else pd.DataFrame()
        normalized_group_levels = groups_df["group"].astype(str).tolist() if not groups_df.empty else group_levels

    variable_results: list[ChiSquareVariableResultData] = []
    for row in summary_df.to_dict(orient="records"):
        variable = str(row["variable"])
        variable_level_rows = levels_df[levels_df["variable"] == variable] if not levels_df.empty else pd.DataFrame()
        grouped_levels: list[ChiSquareLevelRowResult] = []
        if not variable_level_rows.empty:
            for level in variable_level_rows["level"].drop_duplicates().astype(str).tolist():
                level_subset = variable_level_rows[variable_level_rows["level"].astype(str) == level]
                display_map = {
                    str(level_row["group"]): str(level_row["display_value"])
                    for level_row in level_subset.to_dict(orient="records")
                }
                grouped_levels.append(
                    ChiSquareLevelRowResult(
                        level=level,
                        group_values=[display_map.get(group, "-") for group in normalized_group_levels],
                    )
                )

        variable_results.append(
            ChiSquareVariableResultData(
                variable=variable,
                level_rows=grouped_levels,
                minimum_expected_count=_round_nullable(row.get("minimum_expected_count")),
                expected_count_warning=bool(row.get("expected_count_warning", False)),
                recommended_test=str(row.get("recommended_test") or "Chi-squared"),
                executed_test=str(row.get("executed_test") or "Chi-squared"),
                statistic=_round_nullable(row.get("statistic")),
                df=_round_nullable(row.get("df")),
                p_value=_round_nullable(row.get("p_value")),
                note=str(row.get("note") or ""),
            )
        )

    assumptions = [
        "分组变量支持 2 到 4 组，且各组样本需由研究设计保证相互独立。",
        "检验变量应为分类变量；缺失值将在各变量内按完整个案剔除。",
        "程序会先计算列联表和期望频数；若存在期望频数 < 5，将自动切换到 Fisher 精确概率法。",
        "当前分层展示使用的是各水平在该变量内部的构成比，便于快速观察不同组的分布差异。",
    ]

    return ChiSquareExecutionResult(
        dataset_name=dataset_name,
        group_variable=group_variable,
        group_levels=normalized_group_levels,
        alpha=alpha,
        confirm_independence=True,
        assumptions=assumptions,
        variables=variable_results,
    )
