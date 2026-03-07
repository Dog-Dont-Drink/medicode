"""Service for repeated-measures and mixed-design ANOVA workflows via R."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from app.core.exceptions import BadRequest


@dataclass
class RepeatedMeasuresEffectResult:
    statistic: float | None
    df_effect: float | None
    df_error: float | None
    p_value: float | None
    corrected: bool


@dataclass
class RepeatedMeasuresTimeSummaryData:
    time_level: str
    group_level: str | None
    n: int
    mean: float | None
    sd: float | None
    median: float | None
    q1: float | None
    q3: float | None


@dataclass
class RepeatedMeasuresVariableResultData:
    variable: str
    complete_subject_count: int
    excluded_subject_count: int
    duplicate_pair_count: int
    residual_normality_p_value: float | None
    residual_normality_passed: bool
    residual_normality_method: str
    time_sphericity_p_value: float | None
    time_sphericity_passed: bool | None
    time_gg_epsilon: float | None
    time_hf_epsilon: float | None
    interaction_sphericity_p_value: float | None
    interaction_sphericity_passed: bool | None
    interaction_gg_epsilon: float | None
    interaction_hf_epsilon: float | None
    executed_test: str
    note: str
    time_summaries: list[RepeatedMeasuresTimeSummaryData]
    time_effect: RepeatedMeasuresEffectResult
    between_effect: RepeatedMeasuresEffectResult | None
    interaction_effect: RepeatedMeasuresEffectResult | None


@dataclass
class RepeatedMeasuresExecutionResult:
    dataset_name: str
    subject_variable: str
    between_variable: str | None
    between_levels: list[str]
    time_variable: str
    time_levels: list[str]
    alpha: float
    confirm_repeated_design: bool
    assumptions: list[str]
    variables: list[RepeatedMeasuresVariableResultData]


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


def _normalized_levels(series: pd.Series) -> list[str]:
    values = series.dropna().astype(str).tolist()
    seen: set[str] = set()
    levels: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        levels.append(value)
    return levels


def _effect_result_from_row(row: dict[str, object], prefix: str) -> RepeatedMeasuresEffectResult:
    return RepeatedMeasuresEffectResult(
        statistic=_round_nullable(row.get(f"{prefix}_statistic")),
        df_effect=_round_nullable(row.get(f"{prefix}_df_effect")),
        df_error=_round_nullable(row.get(f"{prefix}_df_error")),
        p_value=_round_nullable(row.get(f"{prefix}_p_value")),
        corrected=bool(_parse_boolish(row.get(f"{prefix}_corrected"))),
    )


def _build_time_summaries(
    analysis_df: pd.DataFrame,
    subject_variable: str,
    time_variable: str,
    variable: str,
    time_levels: list[str],
    between_variable: str | None = None,
    between_levels: list[str] | None = None,
) -> tuple[list[RepeatedMeasuresTimeSummaryData], int, int, int]:
    required_subset = [subject_variable, time_variable]
    if between_variable:
        required_subset.append(between_variable)

    if between_variable:
        sub_df = analysis_df[[subject_variable, between_variable, time_variable, variable]].copy()
        sub_df.columns = ["subject", "between", "time", "value"]
    else:
        sub_df = analysis_df[[subject_variable, time_variable, variable]].copy()
        sub_df.columns = ["subject", "time", "value"]
        sub_df["between"] = "overall"

    sub_df = sub_df.dropna(subset=["subject", "time"] + (["between"] if between_variable else []))
    sub_df["value"] = pd.to_numeric(sub_df["value"], errors="coerce")
    sub_df = sub_df.dropna(subset=["value"])
    if sub_df.empty:
        return [], 0, 0, 0

    sub_df["subject"] = sub_df["subject"].astype(str)
    sub_df["time"] = sub_df["time"].astype(str)
    sub_df["between"] = sub_df["between"].astype(str)

    duplicate_pair_count = int(sub_df.duplicated(subset=["subject", "time"]).sum())
    if between_variable:
        agg_df = sub_df.groupby(["subject", "between", "time"], as_index=False)["value"].mean()
        between_check = agg_df.groupby("subject")["between"].nunique()
        valid_subjects = between_check[between_check == 1].index.astype(str)
        agg_df = agg_df[agg_df["subject"].isin(valid_subjects)].copy()
    else:
        agg_df = sub_df.groupby(["subject", "time"], as_index=False)["value"].mean()
        agg_df["between"] = "overall"

    subject_counts = agg_df.groupby("subject")["time"].nunique()
    complete_subjects = subject_counts[subject_counts == len(time_levels)].index.astype(str)
    balanced_df = agg_df[agg_df["subject"].isin(complete_subjects)].copy()
    total_subject_count = int(agg_df["subject"].nunique())
    complete_subject_count = int(balanced_df["subject"].nunique())
    excluded_subject_count = max(total_subject_count - complete_subject_count, 0)

    if balanced_df.empty:
        return [], complete_subject_count, excluded_subject_count, duplicate_pair_count

    summaries: list[RepeatedMeasuresTimeSummaryData] = []
    group_levels_to_use = between_levels if between_variable else [None]
    for time_level in time_levels:
        time_df = balanced_df[balanced_df["time"] == time_level]
        for group_level in group_levels_to_use:
            if between_variable:
                group_df = time_df[time_df["between"] == str(group_level)]
            else:
                group_df = time_df

            values = group_df["value"].astype(float)
            if values.empty:
                summaries.append(
                    RepeatedMeasuresTimeSummaryData(
                        time_level=str(time_level),
                        group_level=None if group_level is None else str(group_level),
                        n=0,
                        mean=None,
                        sd=None,
                        median=None,
                        q1=None,
                        q3=None,
                    )
                )
                continue

            summaries.append(
                RepeatedMeasuresTimeSummaryData(
                    time_level=str(time_level),
                    group_level=None if group_level is None else str(group_level),
                    n=int(values.shape[0]),
                    mean=_round_nullable(values.mean()),
                    sd=_round_nullable(values.std(ddof=1)),
                    median=_round_nullable(values.median()),
                    q1=_round_nullable(values.quantile(0.25)),
                    q3=_round_nullable(values.quantile(0.75)),
                )
            )

    return summaries, complete_subject_count, excluded_subject_count, duplicate_pair_count


def run_repeated_measures_anova(
    df: pd.DataFrame,
    dataset_name: str,
    subject_variable: str,
    time_variable: str,
    continuous_variables: list[str],
    alpha: float,
    confirm_repeated_design: bool,
    between_variable: str | None = None,
) -> RepeatedMeasuresExecutionResult:
    if subject_variable not in df.columns:
        raise BadRequest("受试者标识变量不存在")
    if time_variable not in df.columns:
        raise BadRequest("时间变量不存在")
    if between_variable and between_variable not in df.columns:
        raise BadRequest("组间分组变量不存在")
    if subject_variable == time_variable or (between_variable and subject_variable == between_variable) or (between_variable and between_variable == time_variable):
        raise BadRequest("ID、组间分组变量和时间变量不能重复")
    if not continuous_variables:
        raise BadRequest("请至少选择一个连续变量")

    selected_columns = [subject_variable, time_variable]
    if between_variable:
        selected_columns.append(between_variable)
    selected_columns.extend(continuous_variables)
    analysis_df = df[selected_columns].copy()
    required_subset = [subject_variable, time_variable]
    if between_variable:
        required_subset.append(between_variable)
    analysis_df = analysis_df.dropna(subset=required_subset)

    time_levels = _normalized_levels(analysis_df[time_variable])
    if len(time_levels) < 2 or len(time_levels) > 6:
        raise BadRequest("时间变量仅支持 2 到 6 个水平")

    between_levels = _normalized_levels(analysis_df[between_variable]) if between_variable else []
    if between_variable and (len(between_levels) < 2 or len(between_levels) > 4):
        raise BadRequest("组间分组变量仅支持 2 到 4 个组别")

    invalid_columns = [column for column in continuous_variables if column not in analysis_df.columns]
    if invalid_columns:
        raise BadRequest(f"存在无效连续变量: {', '.join(invalid_columns[:5])}")

    for column in continuous_variables:
        analysis_df[column] = pd.to_numeric(analysis_df[column], errors="coerce")

    non_numeric_columns = [column for column in continuous_variables if not _is_continuous(analysis_df[column])]
    if non_numeric_columns:
        raise BadRequest(f"以下变量不是连续型数值变量: {', '.join(non_numeric_columns[:5])}")

    with tempfile.TemporaryDirectory(prefix="medicode-mixed-rm-anova-") as temp_dir:
        temp_path = Path(temp_dir)
        input_csv = temp_path / "input.csv"
        summary_csv = temp_path / "summary.csv"
        script_path = temp_path / "mixed_repeated_measures_anova.R"

        analysis_df.to_csv(input_csv, index=False, encoding="utf-8-sig")
        r_script = """
args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
summary_csv <- args[2]
subject_var <- args[3]
between_var_arg <- args[4]
time_var <- args[5]
alpha <- as.numeric(args[6])
variables <- strsplit(args[7], "\\t", fixed = FALSE)[[1]]

if (!requireNamespace("car", quietly = TRUE)) {
  stop("R package 'car' is required for repeated-measures ANOVA")
}

normalize_missing <- function(x) {
  x[x %in% c("", "<NA>", "NA", "nan", "NaN")] <- NA
  x
}

extract_effect <- function(univariate_tests, effect_name) {
  if (is.null(univariate_tests) || !(effect_name %in% rownames(univariate_tests))) {
    return(list(
      statistic = NA, df_effect = NA, df_error = NA, p_value = NA, corrected = FALSE
    ))
  }

  row <- univariate_tests[effect_name, ]
  statistic <- unname(row["F value"])
  df_effect <- unname(row["num Df"])
  df_error <- unname(row["den Df"])
  p_value <- unname(row["Pr(>F)"])

  list(
    statistic = statistic,
    df_effect = df_effect,
    df_error = df_error,
    p_value = p_value,
    corrected = FALSE
  )
}

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE)
between_enabled <- between_var_arg != ""

df[[subject_var]] <- as.character(normalize_missing(df[[subject_var]]))
df[[time_var]] <- as.character(normalize_missing(df[[time_var]]))
if (between_enabled) {
  df[[between_var_arg]] <- as.character(normalize_missing(df[[between_var_arg]]))
}

summary_rows <- list()
index <- 1

for (var_name in variables) {
  if (between_enabled) {
    sub_df <- df[, c(subject_var, between_var_arg, time_var, var_name)]
    names(sub_df) <- c("subject", "between", "time", "value")
    sub_df$between <- as.character(normalize_missing(sub_df$between))
    sub_df <- sub_df[complete.cases(sub_df[, c("subject", "between", "time")]), ]
  } else {
    sub_df <- df[, c(subject_var, time_var, var_name)]
    names(sub_df) <- c("subject", "time", "value")
    sub_df$between <- "overall"
    sub_df <- sub_df[complete.cases(sub_df[, c("subject", "time")]), ]
  }

  sub_df$value <- suppressWarnings(as.numeric(normalize_missing(sub_df$value)))
  sub_df <- sub_df[!is.na(sub_df$value), ]
  if (nrow(sub_df) == 0) {
    next
  }

  sub_df$subject <- as.character(sub_df$subject)
  sub_df$between <- as.character(sub_df$between)
  time_levels <- unique(sub_df$time)
  if (length(time_levels) < 2 || length(time_levels) > 6) {
    next
  }
  sub_df$time <- factor(sub_df$time, levels = time_levels)

  duplicate_pair_count <- nrow(sub_df) - nrow(unique(sub_df[, c("subject", "time")]))
  if (between_enabled) {
    agg_df <- aggregate(value ~ subject + between + time, data = sub_df, FUN = mean)
    between_check <- aggregate(between ~ subject, data = agg_df, FUN = function(x) {
      unique_values <- unique(x)
      if (length(unique_values) == 1) unique_values[1] else NA
    })
    names(between_check)[2] <- "between_single"
    agg_df <- merge(agg_df, between_check, by = "subject")
    agg_df <- agg_df[!is.na(agg_df$between_single), ]
    agg_df$between <- agg_df$between_single
    agg_df$between_single <- NULL
  } else {
    agg_df <- aggregate(value ~ subject + time, data = sub_df, FUN = mean)
    agg_df$between <- "overall"
  }

  subject_counts <- table(agg_df$subject)
  complete_subjects <- names(subject_counts[subject_counts == length(time_levels)])
  balanced_df <- agg_df[agg_df$subject %in% complete_subjects, ]
  total_subject_count <- length(unique(agg_df$subject))
  complete_subject_count <- length(unique(balanced_df$subject))
  excluded_subject_count <- total_subject_count - complete_subject_count

  if (complete_subject_count < 2) {
    next
  }

  if (between_enabled) {
    between_levels <- unique(balanced_df$between)
    if (length(between_levels) < 2 || length(between_levels) > 4) {
      next
    }
  }

  balanced_df$subject <- as.character(balanced_df$subject)
  balanced_df$between <- as.factor(balanced_df$between)
  balanced_df$time <- factor(balanced_df$time, levels = time_levels)

  residual_fit <- if (between_enabled) {
    lm(value ~ between * time + factor(subject), data = balanced_df)
  } else {
    lm(value ~ factor(subject) + time, data = balanced_df)
  }
  residual_values <- residuals(residual_fit)
  if (length(residual_values) >= 3 && length(residual_values) <= 5000) {
    residual_normality_p <- shapiro.test(residual_values)$p.value
    residual_normality_method <- "Shapiro-Wilk residual normality"
  } else if (length(residual_values) < 3) {
    residual_normality_p <- NA
    residual_normality_method <- "残差样本量不足"
  } else {
    residual_normality_p <- NA
    residual_normality_method <- "残差样本量过大，未执行 Shapiro"
  }
  residual_normality_passed <- !is.na(residual_normality_p) && residual_normality_p >= alpha

  subject_ids <- sort(unique(balanced_df$subject))
  wide_matrix <- matrix(NA_real_, nrow = length(subject_ids), ncol = length(time_levels))
  rownames(wide_matrix) <- subject_ids
  colnames(wide_matrix) <- time_levels
  between_vector <- rep(NA_character_, length(subject_ids))

  for (row_index in seq_len(nrow(balanced_df))) {
    subject_index <- match(as.character(balanced_df$subject[row_index]), subject_ids)
    time_index <- match(as.character(balanced_df$time[row_index]), time_levels)
    wide_matrix[subject_index, time_index] <- balanced_df$value[row_index]
    between_vector[subject_index] <- as.character(balanced_df$between[row_index])
  }

  wide_df <- as.data.frame(wide_matrix, check.names = FALSE)
  if (between_enabled) {
    wide_df$between <- factor(between_vector)
    mlm_fit <- lm(as.matrix(wide_df[, time_levels, drop = FALSE]) ~ between, data = wide_df)
  } else {
    mlm_fit <- lm(as.matrix(wide_df[, time_levels, drop = FALSE]) ~ 1, data = wide_df)
  }

  idata <- data.frame(time = factor(time_levels, levels = time_levels))
  rm_fit <- car::Anova(mlm_fit, idata = idata, idesign = ~time, type = "III")
  rm_summary <- summary(rm_fit, multivariate = FALSE)

  univariate_tests <- rm_summary$univariate.tests
  sphericity_tests <- rm_summary$sphericity.tests
  adjustments <- rm_summary$pval.adjustments

  time_effect <- extract_effect(univariate_tests, "time")
  between_effect <- if (between_enabled) extract_effect(univariate_tests, "between") else NULL
  interaction_effect <- if (between_enabled) extract_effect(univariate_tests, "between:time") else NULL

  time_sphericity_p <- NA
  time_sphericity_passed <- if (length(time_levels) > 2) NA else TRUE
  interaction_sphericity_p <- NA
  interaction_sphericity_passed <- if (between_enabled && length(time_levels) > 2) NA else NULL
  time_gg <- NA
  time_hf <- NA
  interaction_gg <- NA
  interaction_hf <- NA

  if (!is.null(sphericity_tests) && "time" %in% rownames(sphericity_tests)) {
    time_sphericity_p <- unname(sphericity_tests["time", "p-value"])
    time_sphericity_passed <- !is.na(time_sphericity_p) && time_sphericity_p >= alpha
  }
  if (!is.null(sphericity_tests) && between_enabled && "between:time" %in% rownames(sphericity_tests)) {
    interaction_sphericity_p <- unname(sphericity_tests["between:time", "p-value"])
    interaction_sphericity_passed <- !is.na(interaction_sphericity_p) && interaction_sphericity_p >= alpha
  }
  if (!is.null(adjustments) && "time" %in% rownames(adjustments)) {
    time_gg <- unname(adjustments["time", "GG eps"])
    time_hf <- unname(adjustments["time", "HF eps"])
    if (!is.na(time_sphericity_p) && time_sphericity_p < alpha) {
      gg_p <- unname(adjustments["time", "Pr(>F[GG])"])
      if (!is.na(gg_p)) {
        time_effect$p_value <- gg_p
        time_effect$corrected <- TRUE
      }
    }
  }
  if (!is.null(adjustments) && between_enabled && "between:time" %in% rownames(adjustments)) {
    interaction_gg <- unname(adjustments["between:time", "GG eps"])
    interaction_hf <- unname(adjustments["between:time", "HF eps"])
    if (!is.na(interaction_sphericity_p) && interaction_sphericity_p < alpha) {
      gg_p <- unname(adjustments["between:time", "Pr(>F[GG])"])
      if (!is.na(gg_p)) {
        interaction_effect$p_value <- gg_p
        interaction_effect$corrected <- TRUE
      }
    }
  }

  executed_test <- if (between_enabled) "Mixed repeated measures ANOVA" else "Repeated measures ANOVA"
  note_parts <- c()
  if (between_enabled) {
    note_parts <- c(note_parts, "已纳入组间分组变量与时间变量的交互效应。")
  }
  if (!residual_normality_passed && between_enabled) {
    note_parts <- c(note_parts, "残差正态性未通过，当前仍报告混合设计 ANOVA 结果，解释时需谨慎。")
  } else if (!residual_normality_passed) {
    note_parts <- c(note_parts, "残差正态性未通过，当前仍报告重复测量 ANOVA 结果，解释时需谨慎。")
  }
  if (isTRUE(time_effect$corrected)) {
    note_parts <- c(note_parts, "时间主效应已采用 GG 校正。")
    executed_test <- paste0(executed_test, " (GG corrected)")
  }
  if (between_enabled && !is.null(interaction_effect) && isTRUE(interaction_effect$corrected)) {
    note_parts <- c(note_parts, "交互效应已采用 GG 校正。")
  }
  if (length(note_parts) == 0) {
    note_parts <- c("主要结果满足当前模型设定。")
  }
  note <- paste(note_parts, collapse = " ")

  summary_rows[[index]] <- data.frame(
    variable = var_name,
    complete_subject_count = complete_subject_count,
    excluded_subject_count = excluded_subject_count,
    duplicate_pair_count = duplicate_pair_count,
    residual_normality_p_value = residual_normality_p,
    residual_normality_passed = residual_normality_passed,
    residual_normality_method = residual_normality_method,
    time_sphericity_p_value = time_sphericity_p,
    time_sphericity_passed = ifelse(is.na(time_sphericity_passed), "", time_sphericity_passed),
    time_gg_epsilon = time_gg,
    time_hf_epsilon = time_hf,
    interaction_sphericity_p_value = interaction_sphericity_p,
    interaction_sphericity_passed = ifelse(is.null(interaction_sphericity_passed) || is.na(interaction_sphericity_passed), "", interaction_sphericity_passed),
    interaction_gg_epsilon = interaction_gg,
    interaction_hf_epsilon = interaction_hf,
    executed_test = executed_test,
    note = note,
    time_statistic = time_effect$statistic,
    time_df_effect = time_effect$df_effect,
    time_df_error = time_effect$df_error,
    time_p_value = time_effect$p_value,
    time_corrected = time_effect$corrected,
    between_statistic = ifelse(is.null(between_effect), NA, between_effect$statistic),
    between_df_effect = ifelse(is.null(between_effect), NA, between_effect$df_effect),
    between_df_error = ifelse(is.null(between_effect), NA, between_effect$df_error),
    between_p_value = ifelse(is.null(between_effect), NA, between_effect$p_value),
    between_corrected = ifelse(is.null(between_effect), FALSE, between_effect$corrected),
    interaction_statistic = ifelse(is.null(interaction_effect), NA, interaction_effect$statistic),
    interaction_df_effect = ifelse(is.null(interaction_effect), NA, interaction_effect$df_effect),
    interaction_df_error = ifelse(is.null(interaction_effect), NA, interaction_effect$df_error),
    interaction_p_value = ifelse(is.null(interaction_effect), NA, interaction_effect$p_value),
    interaction_corrected = ifelse(is.null(interaction_effect), FALSE, interaction_effect$corrected)
  )
  index <- index + 1
}

summary_df <- if (length(summary_rows)) do.call(rbind, summary_rows) else data.frame()
write.csv(summary_df, summary_csv, row.names = FALSE)
"""
        script_path.write_text(r_script, encoding="utf-8")
        try:
            subprocess.run(
                [
                    "Rscript",
                    str(script_path),
                    str(input_csv),
                    str(summary_csv),
                    subject_variable,
                    between_variable or "",
                    time_variable,
                    str(alpha),
                    "\t".join(continuous_variables),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise BadRequest("R 混合设计重复测量方差分析执行失败，请确认本机已安装 Rscript 且 car 包可用") from exc

        if not summary_csv.exists():
            raise BadRequest("R 混合设计重复测量方差分析未返回结果")

        summary_df = pd.read_csv(summary_csv)
        if summary_df.empty:
            raise BadRequest("没有可用于重复测量方差分析的有效连续变量，请检查 ID、分组变量、时间变量与缺失值")

    variable_results: list[RepeatedMeasuresVariableResultData] = []
    for row in summary_df.to_dict(orient="records"):
        summaries, complete_subject_count, excluded_subject_count, duplicate_pair_count = _build_time_summaries(
            analysis_df=analysis_df,
            subject_variable=subject_variable,
            time_variable=time_variable,
            variable=str(row["variable"]),
            time_levels=time_levels,
            between_variable=between_variable,
            between_levels=between_levels,
        )
        variable_results.append(
            RepeatedMeasuresVariableResultData(
                variable=str(row["variable"]),
                complete_subject_count=complete_subject_count or int(row.get("complete_subject_count") or 0),
                excluded_subject_count=excluded_subject_count or int(row.get("excluded_subject_count") or 0),
                duplicate_pair_count=duplicate_pair_count or int(row.get("duplicate_pair_count") or 0),
                residual_normality_p_value=_round_nullable(row.get("residual_normality_p_value")),
                residual_normality_passed=bool(_parse_boolish(row.get("residual_normality_passed"))),
                residual_normality_method=str(row.get("residual_normality_method") or ""),
                time_sphericity_p_value=_round_nullable(row.get("time_sphericity_p_value")),
                time_sphericity_passed=_parse_boolish(row.get("time_sphericity_passed")),
                time_gg_epsilon=_round_nullable(row.get("time_gg_epsilon")),
                time_hf_epsilon=_round_nullable(row.get("time_hf_epsilon")),
                interaction_sphericity_p_value=_round_nullable(row.get("interaction_sphericity_p_value")),
                interaction_sphericity_passed=_parse_boolish(row.get("interaction_sphericity_passed")),
                interaction_gg_epsilon=_round_nullable(row.get("interaction_gg_epsilon")),
                interaction_hf_epsilon=_round_nullable(row.get("interaction_hf_epsilon")),
                executed_test=str(row.get("executed_test") or "Mixed repeated measures ANOVA"),
                note=str(row.get("note") or ""),
                time_summaries=summaries,
                time_effect=_effect_result_from_row(row, "time"),
                between_effect=(
                    None
                    if between_variable is None
                    else _effect_result_from_row(row, "between")
                ),
                interaction_effect=(
                    None
                    if between_variable is None
                    else _effect_result_from_row(row, "interaction")
                ),
            )
        )

    assumptions = [
        "请使用长表数据：同一受试者在不同时间水平上占多行记录。",
        "ID 变量用于识别同一受试者；时间变量表示重复测量时点；组间分组变量可选，用于混合设计模型。",
        "每个连续变量会只保留在所有时间水平上均有记录的完整受试者；同一受试者同一时间点的重复记录先取均值。",
        "当提供组间分组变量时，结果会同时报告时间主效应、组间主效应和交互效应；若球形性不满足，则自动采用 GG 校正的 P 值。",
    ]

    return RepeatedMeasuresExecutionResult(
        dataset_name=dataset_name,
        subject_variable=subject_variable,
        between_variable=between_variable,
        between_levels=between_levels,
        time_variable=time_variable,
        time_levels=time_levels,
        alpha=alpha,
        confirm_repeated_design=True,
        assumptions=assumptions,
        variables=variable_results,
    )
