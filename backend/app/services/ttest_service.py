"""Service for running independent-samples t-tests via R."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from app.core.exceptions import BadRequest
from app.services.r_runtime import run_rscript


@dataclass
class TTestGroupSummaryResult:
    group: str
    n: int
    mean: float | None
    sd: float | None
    median: float | None
    q1: float | None
    q3: float | None


@dataclass
class TTestNormalityCheckResult:
    group: str
    n: int
    p_value: float | None
    passed: bool
    method: str


@dataclass
class TTestVariableResultData:
    variable: str
    group_summaries: list[TTestGroupSummaryResult]
    normality_checks: list[TTestNormalityCheckResult]
    variance_test_name: str
    variance_p_value: float | None
    equal_variance: bool | None
    satisfies_t_test: bool
    recommended_test: str
    executed_test: str
    statistic: float | None
    df: float | None
    p_value: float | None
    estimate: float | None
    conf_low: float | None
    conf_high: float | None
    note: str


@dataclass
class TTestExecutionResult:
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    alpha: float
    confirm_independence: bool
    assumptions: list[str]
    variables: list[TTestVariableResultData]


def _round_nullable(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def _is_continuous(series: pd.Series) -> bool:
    return is_numeric_dtype(series) and not is_bool_dtype(series)


def run_ttest(
    df: pd.DataFrame,
    dataset_name: str,
    group_variable: str,
    continuous_variables: list[str],
    alpha: float,
    confirm_independence: bool,
) -> TTestExecutionResult:
    if group_variable not in df.columns:
        raise BadRequest("分组变量不存在")
    if not continuous_variables:
        raise BadRequest("请至少选择一个连续变量")
    analysis_df = df[[group_variable, *continuous_variables]].copy()
    analysis_df = analysis_df.dropna(subset=[group_variable])
    group_levels = analysis_df[group_variable].astype(str).dropna().unique().tolist()
    if len(group_levels) != 2:
        raise BadRequest("T 检验仅支持恰好 2 组的分组变量")

    invalid_columns = [column for column in continuous_variables if column not in analysis_df.columns]
    if invalid_columns:
        raise BadRequest(f"存在无效连续变量: {', '.join(invalid_columns[:5])}")

    for column in continuous_variables:
        analysis_df[column] = pd.to_numeric(analysis_df[column], errors="coerce")

    non_numeric_columns = [column for column in continuous_variables if not _is_continuous(analysis_df[column])]
    if non_numeric_columns:
        raise BadRequest(f"以下变量不是连续型数值变量: {', '.join(non_numeric_columns[:5])}")

    with tempfile.TemporaryDirectory(prefix="medicode-ttest-") as temp_dir:
        temp_path = Path(temp_dir)
        input_csv = temp_path / "input.csv"
        summary_csv = temp_path / "summary.csv"
        normality_csv = temp_path / "normality.csv"
        groups_csv = temp_path / "groups.csv"
        script_path = temp_path / "ttest.R"

        analysis_df.to_csv(input_csv, index=False, encoding="utf-8-sig")
        r_script = """
args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
summary_csv <- args[2]
normality_csv <- args[3]
groups_csv <- args[4]
group_var <- args[5]
alpha <- as.numeric(args[6])
variables <- strsplit(args[7], "\\t", fixed = FALSE)[[1]]

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE)
df[[group_var]] <- as.factor(df[[group_var]])
group_levels <- levels(droplevels(df[[group_var]]))

write.csv(data.frame(group = group_levels), groups_csv, row.names = FALSE)

summary_rows <- list()
normality_rows <- list()
index <- 1

for (var_name in variables) {
  sub_df <- df[, c(group_var, var_name)]
  names(sub_df) <- c("group", "value")
  sub_df$value <- suppressWarnings(as.numeric(sub_df$value))
  sub_df <- sub_df[complete.cases(sub_df), ]
  sub_df$group <- droplevels(as.factor(sub_df$group))
  groups <- levels(sub_df$group)
  if (length(groups) != 2) {
    next
  }

  g1 <- sub_df$value[sub_df$group == groups[1]]
  g2 <- sub_df$value[sub_df$group == groups[2]]

  shapiro_g1 <- if (length(g1) >= 3 && length(g1) <= 5000) shapiro.test(g1)$p.value else NA
  shapiro_g2 <- if (length(g2) >= 3 && length(g2) <= 5000) shapiro.test(g2)$p.value else NA
  normality_method_g1 <- if (length(g1) < 3) "样本量不足" else if (length(g1) > 5000) "样本量过大，未执行 Shapiro" else "Shapiro-Wilk"
  normality_method_g2 <- if (length(g2) < 3) "样本量不足" else if (length(g2) > 5000) "样本量过大，未执行 Shapiro" else "Shapiro-Wilk"
  normality_pass <- !is.na(shapiro_g1) && !is.na(shapiro_g2) && shapiro_g1 >= alpha && shapiro_g2 >= alpha

  variance_p <- NA
  equal_variance <- NA
  variance_test_name <- "F test"
  if (normality_pass && length(g1) >= 2 && length(g2) >= 2) {
    variance_p <- tryCatch(var.test(g1, g2)$p.value, error = function(e) NA)
    equal_variance <- !is.na(variance_p) && variance_p >= alpha
  }

  recommended_test <- if (normality_pass && isTRUE(equal_variance)) "Student t-test" else if (normality_pass) "Welch t-test" else "Mann-Whitney U"
  executed_test <- recommended_test
  test_result <- if (recommended_test == "Student t-test") {
    t.test(g1, g2, var.equal = TRUE, conf.level = 1 - alpha)
  } else if (recommended_test == "Welch t-test") {
    t.test(g1, g2, var.equal = FALSE, conf.level = 1 - alpha)
  } else {
    wilcox.test(g1, g2, conf.int = TRUE, exact = FALSE, conf.level = 1 - alpha)
  }

  note <- if (recommended_test == "Student t-test") {
    "两组均通过正态性检验，且方差齐性成立，适合标准独立样本 t 检验。"
  } else if (recommended_test == "Welch t-test") {
    "两组均通过正态性检验，但方差齐性不足，建议采用 Welch t 检验。"
  } else {
    "至少一组未通过正态性检验或样本量不足，不建议直接使用 t 检验，已给出 Mann-Whitney U 替代结果。"
  }

  summary_rows[[index]] <- data.frame(
    variable = var_name,
    group1 = groups[1],
    group1_n = length(g1),
    group1_mean = mean(g1),
    group1_sd = if (length(g1) > 1) sd(g1) else NA,
    group1_median = median(g1),
    group1_q1 = as.numeric(quantile(g1, 0.25, names = FALSE)),
    group1_q3 = as.numeric(quantile(g1, 0.75, names = FALSE)),
    group2 = groups[2],
    group2_n = length(g2),
    group2_mean = mean(g2),
    group2_sd = if (length(g2) > 1) sd(g2) else NA,
    group2_median = median(g2),
    group2_q1 = as.numeric(quantile(g2, 0.25, names = FALSE)),
    group2_q3 = as.numeric(quantile(g2, 0.75, names = FALSE)),
    variance_test_name = variance_test_name,
    variance_p_value = variance_p,
    equal_variance = ifelse(is.na(equal_variance), "", equal_variance),
    satisfies_t_test = normality_pass,
    recommended_test = recommended_test,
    executed_test = executed_test,
    statistic = unname(test_result$statistic),
    df = ifelse(is.null(test_result$parameter), NA, unname(test_result$parameter)),
    p_value = test_result$p.value,
    estimate = ifelse(is.null(test_result$estimate), NA, unname(test_result$estimate)[1]),
    conf_low = ifelse(is.null(test_result$conf.int), NA, test_result$conf.int[1]),
    conf_high = ifelse(is.null(test_result$conf.int), NA, test_result$conf.int[2]),
    note = note
  )

  normality_rows[[length(normality_rows) + 1]] <- data.frame(
    variable = var_name,
    group = groups[1],
    n = length(g1),
    p_value = shapiro_g1,
    passed = !is.na(shapiro_g1) && shapiro_g1 >= alpha,
    method = normality_method_g1
  )
  normality_rows[[length(normality_rows) + 1]] <- data.frame(
    variable = var_name,
    group = groups[2],
    n = length(g2),
    p_value = shapiro_g2,
    passed = !is.na(shapiro_g2) && shapiro_g2 >= alpha,
    method = normality_method_g2
  )
  index <- index + 1
}

summary_df <- if (length(summary_rows)) do.call(rbind, summary_rows) else data.frame()
normality_df <- if (length(normality_rows)) do.call(rbind, normality_rows) else data.frame()
write.csv(summary_df, summary_csv, row.names = FALSE)
write.csv(normality_df, normality_csv, row.names = FALSE)
"""
        script_path.write_text(r_script, encoding="utf-8")
        run_rscript(
            [
                str(script_path),
                str(input_csv),
                str(summary_csv),
                str(normality_csv),
                str(groups_csv),
                group_variable,
                str(alpha),
                "\t".join(continuous_variables),
            ],
            "R t 检验执行失败",
        )

        if not summary_csv.exists():
            raise BadRequest("R t 检验未返回结果")

        summary_df = pd.read_csv(summary_csv)
        if summary_df.empty:
            raise BadRequest("没有可用于 t 检验的有效连续变量，请检查缺失值和变量类型")

        normality_df = pd.read_csv(normality_csv) if normality_csv.exists() and normality_csv.stat().st_size else pd.DataFrame()
        groups_df = pd.read_csv(groups_csv) if groups_csv.exists() else pd.DataFrame(columns=["group"])
        normalized_group_levels = groups_df["group"].astype(str).tolist() if not groups_df.empty else group_levels

    variable_results: list[TTestVariableResultData] = []
    for row in summary_df.to_dict(orient="records"):
        variable = str(row["variable"])
        normality_rows = normality_df[normality_df["variable"] == variable] if not normality_df.empty else pd.DataFrame()
        variable_results.append(
            TTestVariableResultData(
                variable=variable,
                group_summaries=[
                    TTestGroupSummaryResult(
                        group=str(row["group1"]),
                        n=int(row["group1_n"]),
                        mean=_round_nullable(row.get("group1_mean")),
                        sd=_round_nullable(row.get("group1_sd")),
                        median=_round_nullable(row.get("group1_median")),
                        q1=_round_nullable(row.get("group1_q1")),
                        q3=_round_nullable(row.get("group1_q3")),
                    ),
                    TTestGroupSummaryResult(
                        group=str(row["group2"]),
                        n=int(row["group2_n"]),
                        mean=_round_nullable(row.get("group2_mean")),
                        sd=_round_nullable(row.get("group2_sd")),
                        median=_round_nullable(row.get("group2_median")),
                        q1=_round_nullable(row.get("group2_q1")),
                        q3=_round_nullable(row.get("group2_q3")),
                    ),
                ],
                normality_checks=[
                    TTestNormalityCheckResult(
                        group=str(normality_row["group"]),
                        n=int(normality_row["n"]),
                        p_value=_round_nullable(normality_row.get("p_value")),
                        passed=bool(normality_row.get("passed", False)),
                        method=str(normality_row.get("method") or "Shapiro-Wilk"),
                    )
                    for normality_row in normality_rows.to_dict(orient="records")
                ],
                variance_test_name=str(row.get("variance_test_name") or "F test"),
                variance_p_value=_round_nullable(row.get("variance_p_value")),
                equal_variance=(
                    None if pd.isna(row.get("equal_variance")) or row.get("equal_variance") == "" else str(row.get("equal_variance")).lower() == "true"
                ),
                satisfies_t_test=bool(row.get("satisfies_t_test", False)),
                recommended_test=str(row.get("recommended_test") or "Student t-test"),
                executed_test=str(row.get("executed_test") or "Student t-test"),
                statistic=_round_nullable(row.get("statistic")),
                df=_round_nullable(row.get("df")),
                p_value=_round_nullable(row.get("p_value")),
                estimate=_round_nullable(row.get("estimate")),
                conf_low=_round_nullable(row.get("conf_low")),
                conf_high=_round_nullable(row.get("conf_high")),
                note=str(row.get("note") or ""),
            )
        )

    assumptions = [
        "分组变量必须恰好只有 2 组，且各组样本相互独立。",
        "检验变量需为连续型数值变量，缺失值将在该变量内按完整个案剔除。",
        "每组会自动做 Shapiro-Wilk 正态性检验；若正态性不满足，将提示不宜直接使用 t 检验。",
        "当两组都近似正态时，会继续检查方差齐性；齐性成立用 Student t-test，否则改用 Welch t-test。",
    ]

    return TTestExecutionResult(
        dataset_name=dataset_name,
        group_variable=group_variable,
        group_levels=normalized_group_levels,
        alpha=alpha,
        confirm_independence=True,
        assumptions=assumptions,
        variables=variable_results,
    )
