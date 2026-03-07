from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Literal

import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import BadRequest
from app.services.r_runtime import run_rscript


@dataclass
class LinearRegressionCoefficientData:
    term: str
    estimate: float | None
    std_error: float | None
    statistic: float | None
    p_value: float | None
    conf_low: float | None
    conf_high: float | None


@dataclass
class LinearRegressionExecutionResult:
    dataset_name: str
    outcome_variable: str
    predictor_variables: list[str]
    sample_size: int
    excluded_rows: int
    alpha: float
    r_squared: float | None
    adjusted_r_squared: float | None
    residual_standard_error: float | None
    f_statistic: float | None
    df_model: float | None
    df_residual: float | None
    model_p_value: float | None
    formula: str
    assumptions: list[str]
    coefficients: list[LinearRegressionCoefficientData]
    note: str
    script_r: str


@dataclass
class LogisticRegressionCoefficientData:
    term: str
    odds_ratio: float | None
    std_error: float | None
    z_value: float | None
    p_value: float | None
    conf_low: float | None
    conf_high: float | None


@dataclass
class LogisticRegressionExecutionResult:
    dataset_name: str
    outcome_variable: str
    event_level: str
    reference_level: str
    predictor_variables: list[str]
    sample_size: int
    excluded_rows: int
    alpha: float
    pseudo_r_squared: float | None
    aic: float | None
    null_deviance: float | None
    residual_deviance: float | None
    df_model: float | None
    df_residual: float | None
    model_p_value: float | None
    formula: str
    assumptions: list[str]
    coefficients: list[LogisticRegressionCoefficientData]
    note: str
    script_r: str


@dataclass
class LassoFeatureData:
    term: str
    coefficient_lambda_min: float | None
    coefficient_lambda_1se: float | None
    selected_at_lambda_min: bool
    selected_at_lambda_1se: bool


@dataclass
class LassoPlotData:
    name: str
    filename: str
    media_type: str
    content_base64: str


@dataclass
class LassoRegressionExecutionResult:
    dataset_name: str
    outcome_variable: str
    predictor_variables: list[str]
    family: Literal['gaussian', 'binomial']
    event_level: str | None
    reference_level: str | None
    sample_size: int
    excluded_rows: int
    alpha: float
    lambda_min: float
    lambda_1se: float
    nonzero_count_lambda_min: int
    nonzero_count_lambda_1se: int
    assumptions: list[str]
    selected_features: list[LassoFeatureData]
    plots: list[LassoPlotData]
    note: str
    script_r: str


@dataclass
class CoxRegressionCoefficientData:
    term: str
    hazard_ratio: float | None
    std_error: float | None
    z_value: float | None
    p_value: float | None
    conf_low: float | None
    conf_high: float | None


@dataclass
class CoxRegressionPhTestData:
    term: str
    statistic: float | None
    df: float | None
    p_value: float | None


@dataclass
class CoxRegressionExecutionResult:
    dataset_name: str
    time_variable: str
    event_variable: str
    event_level: str
    reference_level: str
    predictor_variables: list[str]
    sample_size: int
    event_count: int
    excluded_rows: int
    alpha: float
    concordance: float | None
    concordance_std_error: float | None
    likelihood_ratio_statistic: float | None
    likelihood_ratio_df: float | None
    likelihood_ratio_p_value: float | None
    wald_statistic: float | None
    wald_df: float | None
    wald_p_value: float | None
    score_statistic: float | None
    score_df: float | None
    score_p_value: float | None
    global_ph_p_value: float | None
    formula: str
    assumptions: list[str]
    coefficients: list[CoxRegressionCoefficientData]
    proportional_hazards_tests: list[CoxRegressionPhTestData]
    note: str
    script_r: str


def _sanitize_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise BadRequest(f"数据集中缺少变量: {', '.join(missing)}")


def _clean_dataframe(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    subset = df.loc[:, columns].copy()
    for column in subset.columns:
        if subset[column].dtype == object:
            subset[column] = subset[column].map(lambda value: value.strip() if isinstance(value, str) else value)
            subset[column] = subset[column].replace('', pd.NA)
    return subset


def _settings_r_prefix() -> str:
    settings = get_settings()
    auto_install = 'TRUE' if settings.R_AUTO_INSTALL_ENABLED else 'FALSE'
    repo = json.dumps(settings.R_PACKAGE_REPO)
    return f"""
options(repos = c(CRAN = {repo}))
auto_install_enabled <- {auto_install}
ensure_package <- function(pkg) {{
  if (!requireNamespace(pkg, quietly = TRUE)) {{
    if (!isTRUE(auto_install_enabled)) {{
      stop(paste0('缺少 R 包: ', pkg), call. = FALSE)
    }}
    install.packages(pkg, repos = getOption('repos')[['CRAN']])
  }}
}}
`%||%` <- function(x, y) if (is.null(x) || length(x) == 0 || (length(x) == 1 && is.na(x))) y else x
clean_label <- function(x) {{
  if (is.null(x) || length(x) == 0 || is.na(x)) return(NA_character_)
  as.character(x)
}}
backtick <- function(x) paste0('`', gsub('`', '', x, fixed = TRUE), '`')
""".strip()


def _write_dataframe(df: pd.DataFrame, temp_path: Path, name: str) -> Path:
    csv_path = temp_path / name
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def _to_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _encode_plot(path: Path, name: str) -> LassoPlotData:
    return LassoPlotData(
        name=name,
        filename=path.name,
        media_type='image/png',
        content_base64=base64.b64encode(path.read_bytes()).decode('ascii'),
    )


def _is_integer_like_numeric(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors='coerce').dropna()
    if numeric.empty:
        return False
    return bool(((numeric - numeric.round()).abs() < 1e-9).all())


def _resolve_categorical_predictors(
    df: pd.DataFrame,
    predictor_variables: list[str],
    predictor_kind_overrides: dict[str, str] | None = None,
) -> list[str]:
    overrides = predictor_kind_overrides or {}
    categorical_predictors: list[str] = []
    for predictor in predictor_variables:
        series = df[predictor]
        override = overrides.get(predictor)
        if override in {'categorical', 'boolean'}:
            categorical_predictors.append(predictor)
            continue
        if series.dtype == object or pd.api.types.is_bool_dtype(series):
            categorical_predictors.append(predictor)
            continue
        if pd.api.types.is_numeric_dtype(series):
            non_null = pd.to_numeric(series, errors='coerce').dropna()
            unique_count = int(non_null.nunique(dropna=True))
            if 2 <= unique_count <= 6 and _is_integer_like_numeric(non_null):
                categorical_predictors.append(predictor)
    return categorical_predictors


def run_linear_regression(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    alpha: float,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> LinearRegressionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于线性回归')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-linear-regression-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'linear_regression.csv')
        output_path = temp_path / 'linear_regression_output.json'
        script_path = temp_path / 'linear_regression.R'

        script = f"""
{_settings_r_prefix()}
ensure_package('jsonlite')
library(jsonlite)

df <- read.csv({json.dumps(csv_path.as_posix())}, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = 'UTF-8-BOM')
outcome <- {json.dumps(outcome_variable)}
predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(predictor_variables, ensure_ascii=False))}))
categorical_predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(categorical_predictors, ensure_ascii=False))}))
alpha_value <- {alpha}

for (column_name in names(df)) {{
  if (is.character(df[[column_name]])) {{
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ''] <- NA
    df[[column_name]] <- trimmed
  }}
}}

complete_df <- df[stats::complete.cases(df[, c(outcome, predictors), drop = FALSE]), c(outcome, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 5) {{
  stop('有效样本量不足，线性回归至少需要 5 行完整观测。', call. = FALSE)
}}

if (!is.numeric(complete_df[[outcome]])) {{
  stop('线性回归的因变量必须是数值型。', call. = FALSE)
}}

valid_predictors <- c()
for (predictor in predictors) {{
  column <- complete_df[[predictor]]
  unique_values <- unique(column[!is.na(column)])
  if (length(unique_values) >= 2) {{
    if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {{
      complete_df[[predictor]] <- as.factor(column)
    }}
    valid_predictors <- c(valid_predictors, predictor)
  }}
}}

if (length(valid_predictors) == 0) {{
  stop('可用于建模的自变量不足，请检查是否存在单一取值或缺失。', call. = FALSE)
}}

formula_text <- paste(backtick(outcome), '~', paste(vapply(valid_predictors, backtick, character(1)), collapse = ' + '))
fit <- stats::lm(stats::as.formula(formula_text), data = complete_df)
fit_summary <- summary(fit)
coef_matrix <- fit_summary$coefficients
conf_matrix <- suppressMessages(stats::confint(fit, level = 1 - alpha_value))
residual_values <- residuals(fit)

residual_method <- 'Shapiro-Wilk'
residual_p <- NA_real_
residual_note <- '残差正态性未检查'
if (length(residual_values) >= 3 && length(unique(residual_values)) > 1) {{
  if (length(residual_values) <= 5000) {{
    residual_test <- stats::shapiro.test(residual_values)
    residual_p <- residual_test$p.value
    residual_note <- paste0('残差正态性 Shapiro-Wilk P=', formatC(residual_p, format = 'f', digits = 3))
  }} else {{
    residual_method <- '样本量>5000，未执行 Shapiro-Wilk'
    residual_note <- residual_method
  }}
}} else if (length(unique(residual_values)) <= 1) {{
  residual_method <- '残差取值完全相同'
  residual_note <- '残差无离散度，无法执行正态性检验'
}}

coef_df <- data.frame(
  term = rownames(coef_matrix),
  estimate = unname(coef_matrix[, 1]),
  std_error = unname(coef_matrix[, 2]),
  statistic = unname(coef_matrix[, 3]),
  p_value = unname(coef_matrix[, 4]),
  conf_low = unname(conf_matrix[, 1]),
  conf_high = unname(conf_matrix[, 2]),
  check.names = FALSE
)

fstat <- fit_summary$fstatistic
model_p <- if (is.null(fstat)) NA_real_ else stats::pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

result <- list(
  dataset_name = {json.dumps(dataset_name)},
  outcome_variable = outcome,
  predictor_variables = valid_predictors,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  r_squared = unname(fit_summary$r.squared),
  adjusted_r_squared = unname(fit_summary$adj.r.squared),
  residual_standard_error = unname(fit_summary$sigma),
  f_statistic = if (is.null(fstat)) NA_real_ else unname(fstat[1]),
  df_model = if (is.null(fstat)) NA_real_ else unname(fstat[2]),
  df_residual = if (is.null(fstat)) NA_real_ else unname(fstat[3]),
  model_p_value = model_p,
  formula = formula_text,
  assumptions = list(
    '因变量应为连续数值型，自变量可为数值型或分类变量。',
    '模型默认使用完整案例进行拟合，含缺失值的记录已剔除。',
    residual_note,
    '请结合残差图、异常值和共线性进一步判断模型稳健性。'
  ),
  coefficients = coef_df,
  note = paste0('模型共纳入 ', nrow(complete_df), ' 条完整记录；若分类变量存在多个水平，系数以参考水平为基线解释。')
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = 'rows', null = 'null', na = 'null', pretty = TRUE), {json.dumps(output_path.as_posix())})
""".strip()
        script_path.write_text(script, encoding='utf-8')
        run_rscript([script_path.as_posix()], 'R 线性回归执行失败')
        payload = _read_json(output_path)

    return LinearRegressionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        predictor_variables=[str(item) for item in (payload.get('predictor_variables') or predictor_variables)],
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        alpha=_to_float(payload.get('alpha')) or alpha,
        r_squared=_to_float(payload.get('r_squared')),
        adjusted_r_squared=_to_float(payload.get('adjusted_r_squared')),
        residual_standard_error=_to_float(payload.get('residual_standard_error')),
        f_statistic=_to_float(payload.get('f_statistic')),
        df_model=_to_float(payload.get('df_model')),
        df_residual=_to_float(payload.get('df_residual')),
        model_p_value=_to_float(payload.get('model_p_value')),
        formula=str(payload.get('formula') or ''),
        assumptions=[str(item) for item in (payload.get('assumptions') or [])],
        coefficients=[
            LinearRegressionCoefficientData(
                term=str(row.get('term') or ''),
                estimate=_to_float(row.get('estimate')),
                std_error=_to_float(row.get('std_error')),
                statistic=_to_float(row.get('statistic')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
            )
            for row in (payload.get('coefficients') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_logistic_regression(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    alpha: float,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> LogisticRegressionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于 Logistic 回归')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-logistic-regression-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'logistic_regression.csv')
        output_path = temp_path / 'logistic_regression_output.json'
        script_path = temp_path / 'logistic_regression.R'

        script = f"""
{_settings_r_prefix()}
ensure_package('jsonlite')
library(jsonlite)

df <- read.csv({json.dumps(csv_path.as_posix())}, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = 'UTF-8-BOM')
outcome <- {json.dumps(outcome_variable)}
predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(predictor_variables, ensure_ascii=False))}))
categorical_predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(categorical_predictors, ensure_ascii=False))}))
alpha_value <- {alpha}

for (column_name in names(df)) {{
  if (is.character(df[[column_name]])) {{
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ''] <- NA
    df[[column_name]] <- trimmed
  }}
}}

complete_df <- df[stats::complete.cases(df[, c(outcome, predictors), drop = FALSE]), c(outcome, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 10) {{
  stop('有效样本量不足，Logistic 回归至少需要 10 行完整观测。', call. = FALSE)
}}

outcome_values <- unique(complete_df[[outcome]])
outcome_values <- outcome_values[!is.na(outcome_values)]
if (length(outcome_values) != 2) {{
  stop('Logistic 回归因变量必须是二分类变量。', call. = FALSE)
}}

if (is.numeric(complete_df[[outcome]])) {{
  if (!all(sort(unique(complete_df[[outcome]])) %in% c(0, 1))) {{
    stop('数值型 Logistic 因变量仅支持 0/1 编码。', call. = FALSE)
  }}
  reference_level <- '0'
  event_level <- '1'
  complete_df[[outcome]] <- factor(complete_df[[outcome]], levels = c(0, 1), labels = c(reference_level, event_level))
}} else {{
  complete_df[[outcome]] <- factor(complete_df[[outcome]])
  if (nlevels(complete_df[[outcome]]) != 2) {{
    stop('Logistic 回归因变量必须恰好有两个水平。', call. = FALSE)
  }}
  reference_level <- levels(complete_df[[outcome]])[1]
  event_level <- levels(complete_df[[outcome]])[2]
}}

valid_predictors <- c()
for (predictor in predictors) {{
  column <- complete_df[[predictor]]
  unique_values <- unique(column[!is.na(column)])
  if (length(unique_values) >= 2) {{
    if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {{
      complete_df[[predictor]] <- as.factor(column)
    }}
    valid_predictors <- c(valid_predictors, predictor)
  }}
}}
if (length(valid_predictors) == 0) {{
  stop('可用于建模的自变量不足，请检查是否存在单一取值或缺失。', call. = FALSE)
}}

formula_text <- paste(backtick(outcome), '~', paste(vapply(valid_predictors, backtick, character(1)), collapse = ' + '))
fit <- stats::glm(stats::as.formula(formula_text), data = complete_df, family = stats::binomial())
fit_summary <- summary(fit)
coef_matrix <- fit_summary$coefficients
conf_low <- coef_matrix[, 1] - stats::qnorm(1 - alpha_value / 2) * coef_matrix[, 2]
conf_high <- coef_matrix[, 1] + stats::qnorm(1 - alpha_value / 2) * coef_matrix[, 2]
coef_df <- data.frame(
  term = rownames(coef_matrix),
  odds_ratio = unname(exp(coef_matrix[, 1])),
  std_error = unname(coef_matrix[, 2]),
  z_value = unname(coef_matrix[, 3]),
  p_value = unname(coef_matrix[, 4]),
  conf_low = unname(exp(conf_low)),
  conf_high = unname(exp(conf_high)),
  check.names = FALSE
)

model_chisq <- fit$null.deviance - fit$deviance
model_df <- fit$df.null - fit$df.residual
model_p <- stats::pchisq(model_chisq, df = model_df, lower.tail = FALSE)
pseudo_r2 <- if (isTRUE(fit$null.deviance == 0)) NA_real_ else 1 - fit$deviance / fit$null.deviance

result <- list(
  dataset_name = {json.dumps(dataset_name)},
  outcome_variable = outcome,
  event_level = event_level,
  reference_level = reference_level,
  predictor_variables = valid_predictors,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  pseudo_r_squared = pseudo_r2,
  aic = stats::AIC(fit),
  null_deviance = fit$null.deviance,
  residual_deviance = fit$deviance,
  df_model = model_df,
  df_residual = fit$df.residual,
  model_p_value = model_p,
  formula = formula_text,
  assumptions = list(
    '因变量必须是二分类变量，自变量可为数值型或分类变量。',
    '模型默认使用完整案例进行拟合，含缺失值的记录已剔除。',
    'OR > 1 表示事件发生优势升高，OR < 1 表示优势降低。',
    '请进一步检查样本量、稀疏单元和多重共线性，以判断模型稳健性。'
  ),
  coefficients = coef_df,
  note = paste0('事件水平设为 ', event_level, '，参考水平为 ', reference_level, '。')
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = 'rows', null = 'null', na = 'null', pretty = TRUE), {json.dumps(output_path.as_posix())})
""".strip()
        script_path.write_text(script, encoding='utf-8')
        run_rscript([script_path.as_posix()], 'R Logistic 回归执行失败')
        payload = _read_json(output_path)

    return LogisticRegressionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        event_level=str(payload.get('event_level') or ''),
        reference_level=str(payload.get('reference_level') or ''),
        predictor_variables=[str(item) for item in (payload.get('predictor_variables') or predictor_variables)],
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        alpha=_to_float(payload.get('alpha')) or alpha,
        pseudo_r_squared=_to_float(payload.get('pseudo_r_squared')),
        aic=_to_float(payload.get('aic')),
        null_deviance=_to_float(payload.get('null_deviance')),
        residual_deviance=_to_float(payload.get('residual_deviance')),
        df_model=_to_float(payload.get('df_model')),
        df_residual=_to_float(payload.get('df_residual')),
        model_p_value=_to_float(payload.get('model_p_value')),
        formula=str(payload.get('formula') or ''),
        assumptions=[str(item) for item in (payload.get('assumptions') or [])],
        coefficients=[
            LogisticRegressionCoefficientData(
                term=str(row.get('term') or ''),
                odds_ratio=_to_float(row.get('odds_ratio')),
                std_error=_to_float(row.get('std_error')),
                z_value=_to_float(row.get('z_value')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
            )
            for row in (payload.get('coefficients') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_lasso_regression(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    alpha: float,
    nfolds: int,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> LassoRegressionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于 LASSO 回归')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-lasso-regression-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'lasso_regression.csv')
        output_path = temp_path / 'lasso_regression_output.json'
        plot_cv_path = temp_path / 'lasso_cv_curve.png'
        plot_coef_path = temp_path / 'lasso_coefficient_path.png'
        script_path = temp_path / 'lasso_regression.R'

        script = f"""
{_settings_r_prefix()}
ensure_package('jsonlite')
ensure_package('glmnet')
library(jsonlite)
library(glmnet)

df <- read.csv({json.dumps(csv_path.as_posix())}, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = 'UTF-8-BOM')
outcome <- {json.dumps(outcome_variable)}
predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(predictor_variables, ensure_ascii=False))}))
categorical_predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(categorical_predictors, ensure_ascii=False))}))
alpha_value <- {alpha}
nfolds_value <- {nfolds}

for (column_name in names(df)) {{
  if (is.character(df[[column_name]])) {{
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ''] <- NA
    df[[column_name]] <- trimmed
  }}
}}

complete_df <- df[stats::complete.cases(df[, c(outcome, predictors), drop = FALSE]), c(outcome, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < max(10, nfolds_value)) {{
  stop('有效样本量不足，LASSO 回归至少需要不低于折数的完整观测。', call. = FALSE)
}}

family_name <- NA_character_
event_level <- NA_character_
reference_level <- NA_character_
if (is.numeric(complete_df[[outcome]])) {{
  unique_values <- sort(unique(complete_df[[outcome]]))
  if (length(unique_values) == 2 && all(unique_values %in% c(0, 1))) {{
    family_name <- 'binomial'
    reference_level <- '0'
    event_level <- '1'
    y <- as.numeric(complete_df[[outcome]])
  }} else {{
    family_name <- 'gaussian'
    y <- as.numeric(complete_df[[outcome]])
  }}
}} else {{
  complete_df[[outcome]] <- factor(complete_df[[outcome]])
  if (nlevels(complete_df[[outcome]]) == 2) {{
    family_name <- 'binomial'
    reference_level <- levels(complete_df[[outcome]])[1]
    event_level <- levels(complete_df[[outcome]])[2]
    y <- ifelse(complete_df[[outcome]] == event_level, 1, 0)
  }} else {{
    stop('LASSO 当前仅支持连续因变量或二分类因变量。', call. = FALSE)
  }}
}}

for (predictor in predictors) {{
  column <- complete_df[[predictor]]
  if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {{
    complete_df[[predictor]] <- as.factor(column)
  }}
}}

x_formula <- paste('~', paste(vapply(predictors, backtick, character(1)), collapse = ' + '))
x <- stats::model.matrix(stats::as.formula(x_formula), data = complete_df)[, -1, drop = FALSE]
if (ncol(x) == 0) {{
  stop('LASSO 无法构造有效设计矩阵，请检查自变量取值。', call. = FALSE)
}}

set.seed(123)
cv_fit <- glmnet::cv.glmnet(x, y, family = family_name, alpha = 1, nfolds = nfolds_value, standardize = TRUE)
full_fit <- glmnet::glmnet(x, y, family = family_name, alpha = 1, standardize = TRUE)

png(filename = {json.dumps(plot_cv_path.as_posix())}, width = 1600, height = 1200, res = 180)
plot(cv_fit)
title('LASSO Cross-Validation Curve')
dev.off()

png(filename = {json.dumps(plot_coef_path.as_posix())}, width = 1600, height = 1200, res = 180)
plot(full_fit, xvar = 'lambda', label = TRUE)
title('LASSO Coefficient Path')
dev.off()

coef_min <- as.matrix(stats::coef(cv_fit, s = 'lambda.min'))
coef_1se <- as.matrix(stats::coef(cv_fit, s = 'lambda.1se'))
terms_all <- union(rownames(coef_min), rownames(coef_1se))
feature_df <- data.frame(
  term = terms_all,
  coefficient_lambda_min = as.numeric(coef_min[terms_all, 1]),
  coefficient_lambda_1se = as.numeric(coef_1se[terms_all, 1]),
  stringsAsFactors = FALSE,
  check.names = FALSE
)
feature_df$selected_at_lambda_min <- abs(feature_df$coefficient_lambda_min) > 0
feature_df$selected_at_lambda_1se <- abs(feature_df$coefficient_lambda_1se) > 0
feature_df <- feature_df[feature_df$term != '(Intercept)', , drop = FALSE]
feature_df <- feature_df[feature_df$selected_at_lambda_min | feature_df$selected_at_lambda_1se, , drop = FALSE]

result <- list(
  dataset_name = {json.dumps(dataset_name)},
  outcome_variable = outcome,
  predictor_variables = predictors,
  family = family_name,
  event_level = event_level,
  reference_level = reference_level,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  lambda_min = unname(cv_fit$lambda.min),
  lambda_1se = unname(cv_fit$lambda.1se),
  nonzero_count_lambda_min = sum(abs(as.matrix(coef(cv_fit, s = 'lambda.min'))[-1, 1]) > 0),
  nonzero_count_lambda_1se = sum(abs(as.matrix(coef(cv_fit, s = 'lambda.1se'))[-1, 1]) > 0),
  assumptions = list(
    'LASSO 通过 L1 惩罚进行变量筛选，适合高维或存在共线性的候选变量场景。',
    'lambda.min 通常给出预测误差最低的模型，lambda.1se 更保守、变量更少。',
    '图 1 为交叉验证曲线，图 2 为系数路径图，可辅助判断惩罚强度与变量进入顺序。',
    if (family_name == 'binomial') '当前按二分类结局拟合 LASSO Logistic 回归。' else '当前按连续结局拟合 LASSO 线性回归。'
  ),
  selected_features = feature_df,
  note = paste0('设计矩阵共 ', ncol(x), ' 列，建议结合 lambda.min 与 lambda.1se 两套结果综合判断变量筛选。')
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = 'rows', null = 'null', na = 'null', pretty = TRUE), {json.dumps(output_path.as_posix())})
""".strip()
        script_path.write_text(script, encoding='utf-8')
        run_rscript([script_path.as_posix()], 'R LASSO 回归执行失败')
        payload = _read_json(output_path)
        if not plot_cv_path.exists() or not plot_coef_path.exists():
            raise BadRequest('LASSO 图像生成失败')
        plots = [
            _encode_plot(plot_cv_path, '交叉验证曲线'),
            _encode_plot(plot_coef_path, '系数路径图'),
        ]

    return LassoRegressionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        predictor_variables=[str(item) for item in (payload.get('predictor_variables') or predictor_variables)],
        family=str(payload.get('family') or 'gaussian'),
        event_level=str(payload.get('event_level')) if payload.get('event_level') is not None else None,
        reference_level=str(payload.get('reference_level')) if payload.get('reference_level') is not None else None,
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        alpha=_to_float(payload.get('alpha')) or alpha,
        lambda_min=_to_float(payload.get('lambda_min')) or 0.0,
        lambda_1se=_to_float(payload.get('lambda_1se')) or 0.0,
        nonzero_count_lambda_min=_to_int(payload.get('nonzero_count_lambda_min')),
        nonzero_count_lambda_1se=_to_int(payload.get('nonzero_count_lambda_1se')),
        assumptions=[str(item) for item in (payload.get('assumptions') or [])],
        selected_features=[
            LassoFeatureData(
                term=str(row.get('term') or ''),
                coefficient_lambda_min=_to_float(row.get('coefficient_lambda_min')),
                coefficient_lambda_1se=_to_float(row.get('coefficient_lambda_1se')),
                selected_at_lambda_min=bool(row.get('selected_at_lambda_min', False)),
                selected_at_lambda_1se=bool(row.get('selected_at_lambda_1se', False)),
            )
            for row in (payload.get('selected_features') or [])
        ],
        plots=plots,
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_cox_regression(
    df: pd.DataFrame,
    dataset_name: str,
    time_variable: str,
    event_variable: str,
    predictor_variables: list[str],
    alpha: float,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> CoxRegressionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于 Cox 生存分析')

    columns = [time_variable, event_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-cox-regression-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'cox_regression.csv')
        output_path = temp_path / 'cox_regression_output.json'
        script_path = temp_path / 'cox_regression.R'

        script = f"""
{_settings_r_prefix()}
ensure_package('jsonlite')
ensure_package('survival')
library(jsonlite)
library(survival)

df <- read.csv({json.dumps(csv_path.as_posix())}, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = 'UTF-8-BOM')
time_var <- {json.dumps(time_variable)}
event_var <- {json.dumps(event_variable)}
predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(predictor_variables, ensure_ascii=False))}))
categorical_predictors <- unlist(jsonlite::fromJSON({json.dumps(json.dumps(categorical_predictors, ensure_ascii=False))}))
alpha_value <- {alpha}

for (column_name in names(df)) {{
  if (is.character(df[[column_name]])) {{
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ''] <- NA
    df[[column_name]] <- trimmed
  }}
}}

complete_df <- df[stats::complete.cases(df[, c(time_var, event_var, predictors), drop = FALSE]), c(time_var, event_var, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 10) {{
  stop('有效样本量不足，Cox 生存分析至少需要 10 行完整观测。', call. = FALSE)
}}

complete_df[[time_var]] <- suppressWarnings(as.numeric(complete_df[[time_var]]))
if (any(is.na(complete_df[[time_var]]))) {{
  stop('生存时间变量必须是数值型。', call. = FALSE)
}}
if (any(complete_df[[time_var]] <= 0)) {{
  stop('生存时间变量必须大于 0。', call. = FALSE)
}}

event_values <- unique(complete_df[[event_var]])
event_values <- event_values[!is.na(event_values)]
if (length(event_values) != 2) {{
  stop('结局事件变量必须是二分类变量。', call. = FALSE)
}}

if (is.numeric(complete_df[[event_var]])) {{
  numeric_values <- sort(unique(as.numeric(complete_df[[event_var]])))
  if (!all(numeric_values %in% c(0, 1))) {{
    stop('数值型事件变量仅支持 0/1 编码。', call. = FALSE)
  }}
  reference_level <- '0'
  event_level <- '1'
  complete_df$event_status <- as.numeric(complete_df[[event_var]])
}} else {{
  complete_df[[event_var]] <- factor(complete_df[[event_var]])
  if (nlevels(complete_df[[event_var]]) != 2) {{
    stop('结局事件变量必须恰好有两个水平。', call. = FALSE)
  }}
  reference_level <- levels(complete_df[[event_var]])[1]
  event_level <- levels(complete_df[[event_var]])[2]
  complete_df$event_status <- ifelse(complete_df[[event_var]] == event_level, 1, 0)
}}

if (!any(complete_df$event_status == 1)) {{
  stop('当前完整记录中没有事件发生，无法执行 Cox 生存分析。', call. = FALSE)
}}
if (!any(complete_df$event_status == 0)) {{
  stop('当前完整记录中没有删失样本，无法执行 Cox 生存分析。', call. = FALSE)
}}

valid_predictors <- c()
for (predictor in predictors) {{
  column <- complete_df[[predictor]]
  unique_values <- unique(column[!is.na(column)])
  if (length(unique_values) >= 2) {{
    if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {{
      complete_df[[predictor]] <- as.factor(column)
    }}
    valid_predictors <- c(valid_predictors, predictor)
  }}
}}

if (length(valid_predictors) == 0) {{
  stop('可用于建模的自变量不足，请检查是否存在单一取值或缺失。', call. = FALSE)
}}

formula_text <- paste0('survival::Surv(', backtick(time_var), ', event_status) ~ ', paste(vapply(valid_predictors, backtick, character(1)), collapse = ' + '))
fit <- survival::coxph(stats::as.formula(formula_text), data = complete_df, x = TRUE, model = TRUE)
fit_summary <- summary(fit)
coef_matrix <- fit_summary$coefficients
conf_matrix <- fit_summary$conf.int

coef_df <- data.frame(
  term = rownames(coef_matrix),
  hazard_ratio = unname(conf_matrix[, 'exp(coef)']),
  std_error = unname(coef_matrix[, 'se(coef)']),
  z_value = unname(coef_matrix[, 'z']),
  p_value = unname(coef_matrix[, 'Pr(>|z|)']),
  conf_low = unname(conf_matrix[, 'lower .95']),
  conf_high = unname(conf_matrix[, 'upper .95']),
  check.names = FALSE
)

ph_global_p <- NA_real_
ph_rows <- data.frame(term = character(0), statistic = numeric(0), df = numeric(0), p_value = numeric(0), stringsAsFactors = FALSE)
ph_note <- '比例风险假设检验未执行'
ph_result <- tryCatch(survival::cox.zph(fit, transform = 'km'), error = function(e) NULL)
if (!is.null(ph_result)) {{
  ph_table <- as.data.frame(ph_result$table)
  ph_table$term <- rownames(ph_table)
  if ('GLOBAL' %in% ph_table$term) {{
    ph_global_p <- ph_table[ph_table$term == 'GLOBAL', 'p'][1]
    ph_rows <- ph_table[ph_table$term != 'GLOBAL', c('term', 'chisq', 'df', 'p'), drop = FALSE]
    colnames(ph_rows) <- c('term', 'statistic', 'df', 'p_value')
  }} else {{
    ph_rows <- ph_table[, c('term', 'chisq', 'df', 'p'), drop = FALSE]
    colnames(ph_rows) <- c('term', 'statistic', 'df', 'p_value')
  }}
  ph_note <- if (is.na(ph_global_p)) 'cox.zph 已执行，但未返回全局 P 值。' else paste0('Schoenfeld 残差全局检验 P=', formatC(ph_global_p, format = 'f', digits = 3))
}}

concordance_value <- NA_real_
concordance_se <- NA_real_
if (!is.null(fit_summary$concordance) && length(fit_summary$concordance) >= 2) {{
  concordance_value <- unname(fit_summary$concordance[1])
  concordance_se <- unname(fit_summary$concordance[2])
}}

logtest <- fit_summary$logtest
waldtest <- fit_summary$waldtest
sctest <- fit_summary$sctest

result <- list(
  dataset_name = {json.dumps(dataset_name)},
  time_variable = time_var,
  event_variable = event_var,
  event_level = event_level,
  reference_level = reference_level,
  predictor_variables = valid_predictors,
  sample_size = nrow(complete_df),
  event_count = sum(complete_df$event_status == 1),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  concordance = concordance_value,
  concordance_std_error = concordance_se,
  likelihood_ratio_statistic = if (is.null(logtest)) NA_real_ else unname(logtest[1]),
  likelihood_ratio_df = if (is.null(logtest)) NA_real_ else unname(logtest[2]),
  likelihood_ratio_p_value = if (is.null(logtest)) NA_real_ else unname(logtest[3]),
  wald_statistic = if (is.null(waldtest)) NA_real_ else unname(waldtest[1]),
  wald_df = if (is.null(waldtest)) NA_real_ else unname(waldtest[2]),
  wald_p_value = if (is.null(waldtest)) NA_real_ else unname(waldtest[3]),
  score_statistic = if (is.null(sctest)) NA_real_ else unname(sctest[1]),
  score_df = if (is.null(sctest)) NA_real_ else unname(sctest[2]),
  score_p_value = if (is.null(sctest)) NA_real_ else unname(sctest[3]),
  global_ph_p_value = ph_global_p,
  formula = formula_text,
  assumptions = list(
    '生存时间变量必须为连续正数，事件变量必须为二分类变量。',
    '模型默认使用完整案例进行拟合，含缺失值的记录已剔除。',
    'HR > 1 表示事件风险升高，HR < 1 表示事件风险降低。',
    ph_note
  ),
  coefficients = coef_df,
  proportional_hazards_tests = ph_rows,
  note = paste0('事件水平设为 ', event_level, '，参考水平为 ', reference_level, '；完整样本中共观察到 ', sum(complete_df$event_status == 1), ' 个事件。')
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = 'rows', null = 'null', na = 'null', pretty = TRUE), {json.dumps(output_path.as_posix())})
""".strip()
        script_path.write_text(script, encoding='utf-8')
        run_rscript([script_path.as_posix()], 'R Cox 生存分析执行失败')
        payload = _read_json(output_path)

    return CoxRegressionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        time_variable=str(payload.get('time_variable') or time_variable),
        event_variable=str(payload.get('event_variable') or event_variable),
        event_level=str(payload.get('event_level') or ''),
        reference_level=str(payload.get('reference_level') or ''),
        predictor_variables=[str(item) for item in (payload.get('predictor_variables') or predictor_variables)],
        sample_size=_to_int(payload.get('sample_size')),
        event_count=_to_int(payload.get('event_count')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        alpha=_to_float(payload.get('alpha')) or alpha,
        concordance=_to_float(payload.get('concordance')),
        concordance_std_error=_to_float(payload.get('concordance_std_error')),
        likelihood_ratio_statistic=_to_float(payload.get('likelihood_ratio_statistic')),
        likelihood_ratio_df=_to_float(payload.get('likelihood_ratio_df')),
        likelihood_ratio_p_value=_to_float(payload.get('likelihood_ratio_p_value')),
        wald_statistic=_to_float(payload.get('wald_statistic')),
        wald_df=_to_float(payload.get('wald_df')),
        wald_p_value=_to_float(payload.get('wald_p_value')),
        score_statistic=_to_float(payload.get('score_statistic')),
        score_df=_to_float(payload.get('score_df')),
        score_p_value=_to_float(payload.get('score_p_value')),
        global_ph_p_value=_to_float(payload.get('global_ph_p_value')),
        formula=str(payload.get('formula') or ''),
        assumptions=[str(item) for item in (payload.get('assumptions') or [])],
        coefficients=[
            CoxRegressionCoefficientData(
                term=str(row.get('term') or ''),
                hazard_ratio=_to_float(row.get('hazard_ratio')),
                std_error=_to_float(row.get('std_error')),
                z_value=_to_float(row.get('z_value')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
            )
            for row in (payload.get('coefficients') or [])
        ],
        proportional_hazards_tests=[
            CoxRegressionPhTestData(
                term=str(row.get('term') or ''),
                statistic=_to_float(row.get('statistic')),
                df=_to_float(row.get('df')),
                p_value=_to_float(row.get('p_value')),
            )
            for row in (payload.get('proportional_hazards_tests') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
    )
