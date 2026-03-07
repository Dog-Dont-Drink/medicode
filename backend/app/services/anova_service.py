"""Service for running one-way ANOVA workflows via R."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from app.core.exceptions import BadRequest


@dataclass
class AnovaGroupSummaryResult:
    group: str
    n: int
    mean: float | None
    sd: float | None
    median: float | None
    q1: float | None
    q3: float | None


@dataclass
class AnovaNormalityCheckResult:
    group: str
    n: int
    p_value: float | None
    passed: bool
    method: str


@dataclass
class AnovaVariableResultData:
    variable: str
    group_summaries: list[AnovaGroupSummaryResult]
    normality_checks: list[AnovaNormalityCheckResult]
    variance_test_name: str
    variance_p_value: float | None
    equal_variance: bool | None
    satisfies_anova: bool
    recommended_test: str
    executed_test: str
    statistic: float | None
    df_between: float | None
    df_within: float | None
    p_value: float | None
    note: str


@dataclass
class AnovaExecutionResult:
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    alpha: float
    confirm_independence: bool
    assumptions: list[str]
    variables: list[AnovaVariableResultData]


def _round_nullable(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def _parse_boolish(value) -> bool | None:
    if value is None or pd.isna(value):
        return None
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def _is_continuous(series: pd.Series) -> bool:
    return is_numeric_dtype(series) and not is_bool_dtype(series)


def run_anova(
    df: pd.DataFrame,
    dataset_name: str,
    group_variable: str,
    continuous_variables: list[str],
    alpha: float,
    confirm_independence: bool,
) -> AnovaExecutionResult:
    if group_variable not in df.columns:
        raise BadRequest("分组变量不存在")
    if not continuous_variables:
        raise BadRequest("请至少选择一个连续变量")
    analysis_df = df[[group_variable, *continuous_variables]].copy()
    analysis_df = analysis_df.dropna(subset=[group_variable])
    group_levels = analysis_df[group_variable].astype(str).dropna().unique().tolist()
    if len(group_levels) < 3 or len(group_levels) > 4:
        raise BadRequest("方差分析仅支持 3 到 4 组的分组变量")

    invalid_columns = [column for column in continuous_variables if column not in analysis_df.columns]
    if invalid_columns:
        raise BadRequest(f"存在无效连续变量: {', '.join(invalid_columns[:5])}")

    for column in continuous_variables:
        analysis_df[column] = pd.to_numeric(analysis_df[column], errors="coerce")

    non_numeric_columns = [column for column in continuous_variables if not _is_continuous(analysis_df[column])]
    if non_numeric_columns:
        raise BadRequest(f"以下变量不是连续型数值变量: {', '.join(non_numeric_columns[:5])}")

    with tempfile.TemporaryDirectory(prefix="medicode-anova-") as temp_dir:
        temp_path = Path(temp_dir)
        input_csv = temp_path / "input.csv"
        summary_csv = temp_path / "summary.csv"
        normality_csv = temp_path / "normality.csv"
        groups_csv = temp_path / "groups.csv"
        group_summary_csv = temp_path / "group_summary.csv"

        analysis_df.to_csv(input_csv, index=False, encoding="utf-8-sig")
        r_script = """
args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
summary_csv <- args[2]
normality_csv <- args[3]
groups_csv <- args[4]
group_summary_csv <- args[5]
group_var <- args[6]
alpha <- as.numeric(args[7])
variables <- strsplit(args[8], "\\t", fixed = FALSE)[[1]]

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE)
df[[group_var]] <- as.factor(df[[group_var]])
group_levels <- levels(droplevels(df[[group_var]]))

write.csv(data.frame(group = group_levels), groups_csv, row.names = FALSE)

summary_rows <- list()
normality_rows <- list()
group_rows <- list()
index <- 1

for (var_name in variables) {
  sub_df <- df[, c(group_var, var_name)]
  names(sub_df) <- c("group", "value")
  sub_df$value <- suppressWarnings(as.numeric(sub_df$value))
  sub_df <- sub_df[complete.cases(sub_df), ]
  sub_df$group <- droplevels(as.factor(sub_df$group))
  groups <- levels(sub_df$group)
  if (length(groups) < 3 || length(groups) > 4) {
    next
  }

  normality_pass <- TRUE
  all_groups_large_enough <- TRUE
  for (group_name in groups) {
    g <- sub_df$value[sub_df$group == group_name]
    shapiro_p <- if (length(g) >= 3 && length(g) <= 5000) shapiro.test(g)$p.value else NA
    method <- if (length(g) < 3) "样本量不足" else if (length(g) > 5000) "样本量过大，未执行 Shapiro" else "Shapiro-Wilk"
    passed <- !is.na(shapiro_p) && shapiro_p >= alpha
    if (!passed) {
      normality_pass <- FALSE
    }
    if (length(g) < 3) {
      all_groups_large_enough <- FALSE
    }

    group_rows[[length(group_rows) + 1]] <- data.frame(
      variable = var_name,
      group = group_name,
      n = length(g),
      mean = mean(g),
      sd = if (length(g) > 1) sd(g) else NA,
      median = median(g),
      q1 = as.numeric(quantile(g, 0.25, names = FALSE)),
      q3 = as.numeric(quantile(g, 0.75, names = FALSE))
    )

    normality_rows[[length(normality_rows) + 1]] <- data.frame(
      variable = var_name,
      group = group_name,
      n = length(g),
      p_value = shapiro_p,
      passed = passed,
      method = method
    )
  }

  variance_test_name <- "Bartlett test"
  variance_p <- NA
  equal_variance <- NA
  if (normality_pass && all_groups_large_enough) {
    variance_p <- tryCatch(bartlett.test(value ~ group, data = sub_df)$p.value, error = function(e) NA)
    equal_variance <- !is.na(variance_p) && variance_p >= alpha
  }

  use_anova <- normality_pass && isTRUE(equal_variance)
  executed_test <- if (use_anova) "One-way ANOVA" else "Kruskal-Wallis"
  recommended_test <- executed_test

  if (use_anova) {
    fit <- aov(value ~ group, data = sub_df)
    fit_summary <- summary(fit)[[1]]
    statistic <- fit_summary[1, "F value"]
    df_between <- fit_summary[1, "Df"]
    df_within <- fit_summary[2, "Df"]
    p_value <- fit_summary[1, "Pr(>F)"]
    note <- "各组均通过正态性检验，且 Bartlett 方差齐性成立，采用单因素方差分析。"
  } else {
    kw <- kruskal.test(value ~ group, data = sub_df)
    statistic <- unname(kw$statistic)
    df_between <- ifelse(is.null(kw$parameter), NA, unname(kw$parameter))
    df_within <- NA
    p_value <- kw$p.value
    if (!normality_pass) {
      note <- "至少一组未通过正态性检验或样本量不足，不满足方差分析前提，已改用 Kruskal-Wallis 检验。"
    } else {
      note <- "正态性基本满足，但方差齐性不足，不建议直接使用方差分析，已改用 Kruskal-Wallis 检验。"
    }
  }

  summary_rows[[index]] <- data.frame(
    variable = var_name,
    variance_test_name = variance_test_name,
    variance_p_value = variance_p,
    equal_variance = ifelse(is.na(equal_variance), "", equal_variance),
    satisfies_anova = use_anova,
    recommended_test = recommended_test,
    executed_test = executed_test,
    statistic = statistic,
    df_between = df_between,
    df_within = df_within,
    p_value = p_value,
    note = note
  )
  index <- index + 1
}

summary_df <- if (length(summary_rows)) do.call(rbind, summary_rows) else data.frame()
normality_df <- if (length(normality_rows)) do.call(rbind, normality_rows) else data.frame()
group_summary_df <- if (length(group_rows)) do.call(rbind, group_rows) else data.frame()
write.csv(summary_df, summary_csv, row.names = FALSE)
write.csv(normality_df, normality_csv, row.names = FALSE)
write.csv(group_summary_df, group_summary_csv, row.names = FALSE)
"""
        try:
            subprocess.run(
                [
                    "Rscript",
                    "-e",
                    r_script,
                    str(input_csv),
                    str(summary_csv),
                    str(normality_csv),
                    str(groups_csv),
                    str(group_summary_csv),
                    group_variable,
                    str(alpha),
                    "\t".join(continuous_variables),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise BadRequest("R 方差分析执行失败，请确认本机已安装 Rscript 且数据格式正确") from exc

        if not summary_csv.exists():
            raise BadRequest("R 方差分析未返回结果")

        summary_df = pd.read_csv(summary_csv)
        if summary_df.empty:
            raise BadRequest("没有可用于方差分析的有效连续变量，请检查缺失值和变量类型")

        normality_df = pd.read_csv(normality_csv) if normality_csv.exists() and normality_csv.stat().st_size else pd.DataFrame()
        groups_df = pd.read_csv(groups_csv) if groups_csv.exists() else pd.DataFrame(columns=["group"])
        group_summary_df = (
            pd.read_csv(group_summary_csv)
            if group_summary_csv.exists() and group_summary_csv.stat().st_size
            else pd.DataFrame()
        )
        normalized_group_levels = groups_df["group"].astype(str).tolist() if not groups_df.empty else group_levels

    variable_results: list[AnovaVariableResultData] = []
    for row in summary_df.to_dict(orient="records"):
        variable = str(row["variable"])
        variable_normality_rows = normality_df[normality_df["variable"] == variable] if not normality_df.empty else pd.DataFrame()
        variable_group_rows = group_summary_df[group_summary_df["variable"] == variable] if not group_summary_df.empty else pd.DataFrame()
        variable_results.append(
            AnovaVariableResultData(
                variable=variable,
                group_summaries=[
                    AnovaGroupSummaryResult(
                        group=str(group_row["group"]),
                        n=int(group_row["n"]),
                        mean=_round_nullable(group_row.get("mean")),
                        sd=_round_nullable(group_row.get("sd")),
                        median=_round_nullable(group_row.get("median")),
                        q1=_round_nullable(group_row.get("q1")),
                        q3=_round_nullable(group_row.get("q3")),
                    )
                    for group_row in variable_group_rows.to_dict(orient="records")
                ],
                normality_checks=[
                    AnovaNormalityCheckResult(
                        group=str(normality_row["group"]),
                        n=int(normality_row["n"]),
                        p_value=_round_nullable(normality_row.get("p_value")),
                        passed=bool(normality_row.get("passed", False)),
                        method=str(normality_row.get("method") or "Shapiro-Wilk"),
                    )
                    for normality_row in variable_normality_rows.to_dict(orient="records")
                ],
                variance_test_name=str(row.get("variance_test_name") or "Bartlett test"),
                variance_p_value=_round_nullable(row.get("variance_p_value")),
                equal_variance=_parse_boolish(row.get("equal_variance")),
                satisfies_anova=bool(row.get("satisfies_anova", False)),
                recommended_test=str(row.get("recommended_test") or "One-way ANOVA"),
                executed_test=str(row.get("executed_test") or "One-way ANOVA"),
                statistic=_round_nullable(row.get("statistic")),
                df_between=_round_nullable(row.get("df_between")),
                df_within=_round_nullable(row.get("df_within")),
                p_value=_round_nullable(row.get("p_value")),
                note=str(row.get("note") or ""),
            )
        )

    assumptions = [
        "分组变量需为 3 到 4 组，且各组样本相互独立。",
        "检验变量需为连续型数值变量，缺失值将在各变量内按完整个案剔除。",
        "程序会对每组执行 Shapiro-Wilk 正态性检验，并以 Bartlett test 检查方差齐性。",
        "若正态性或方差齐性不满足，将自动改用 Kruskal-Wallis 多组非参数检验。",
    ]

    return AnovaExecutionResult(
        dataset_name=dataset_name,
        group_variable=group_variable,
        group_levels=normalized_group_levels,
        alpha=alpha,
        confirm_independence=True,
        assumptions=assumptions,
        variables=variable_results,
    )
