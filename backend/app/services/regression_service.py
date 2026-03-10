from __future__ import annotations

import base64
from dataclasses import dataclass, field
import json
from pathlib import Path
import tempfile
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from app.core.exceptions import BadRequest
from app.services.r_runtime import get_r_script_path, load_r_script, run_rscript
from app.services.dataset_parser import load_tabular_dataframe


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
    residual_normality_method: str
    residual_normality_p_value: float | None
    residual_normality_passed: bool
    homoscedasticity_test_method: str
    homoscedasticity_p_value: float | None
    homoscedasticity_passed: bool
    coefficients: list[LinearRegressionCoefficientData]
    plots: list[LassoPlotData]
    note: str
    script_r: str


@dataclass
class LogisticRegressionCoefficientData:
    term: str
    coefficient: float | None
    odds_ratio: float | None
    std_error: float | None
    z_value: float | None
    p_value: float | None
    conf_low: float | None
    conf_high: float | None


@dataclass
class UnivariateScreenCoefficientData:
    predictor: str
    term: str
    coefficient: float | None
    effect_value: float | None
    std_error: float | None
    statistic: float | None
    p_value: float | None
    conf_low: float | None
    conf_high: float | None
    selected: bool


@dataclass
class UnivariateScreenExecutionResult:
    dataset_name: str
    analysis_kind: Literal['linear', 'logistic', 'cox']
    outcome_variable: str | None
    time_variable: str | None
    event_variable: str | None
    sample_size: int
    excluded_rows: int
    selection_mode: Literal['threshold', 'display_only']
    threshold: float | None
    effect_label: str
    selected_predictors: list[str]
    coefficients: list[UnivariateScreenCoefficientData]
    note: str
    script_r: str


@dataclass
class MissingValueExecutionResult:
    dataset_name: str
    method: str
    threshold: float
    input_rows: int
    input_columns: int
    output_rows: int
    output_columns: int
    removed_rows: int
    removed_columns: int
    removed_column_names: list[str]
    numeric_imputed_cells: int
    categorical_imputed_cells: int
    missing_cells_before: int
    missing_cells_after: int
    processed_columns: list[str]
    output_name: str
    operations: list[str]
    cleaned_df: pd.DataFrame
    csv_content: bytes
    script_r: str


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
    univariate_coefficients: list[LogisticRegressionCoefficientData]
    coefficients: list[LogisticRegressionCoefficientData]
    plots: list[LassoPlotData]
    note: str
    script_r: str
    metrics: list["BinaryModelMetricData"] = field(default_factory=list)
    hosmer_lemeshow_p_value: float | None = None


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
    vector_pdf_filename: str | None = None
    vector_pdf_base64: str | None = None


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
class RandomForestImportanceFeatureData:
    predictor: str
    importance: float | None
    secondary_importance: float | None
    normalized_importance: float | None
    rank: int
    selected: bool


@dataclass
class RandomForestSelectionExecutionResult:
    dataset_name: str
    outcome_variable: str
    predictor_variables: list[str]
    family: Literal['gaussian', 'binomial']
    event_level: str | None
    reference_level: str | None
    sample_size: int
    excluded_rows: int
    trees: int
    top_n: int
    importance_metric: str
    secondary_metric: str | None
    selected_predictors: list[str]
    importance_rows: list[RandomForestImportanceFeatureData]
    plots: list[LassoPlotData]
    note: str
    script_r: str


@dataclass
class BorutaFeatureData:
    predictor: str
    decision: str
    mean_importance: float | None
    median_importance: float | None
    min_importance: float | None
    max_importance: float | None
    normalized_hits: float | None
    selected: bool


@dataclass
class BorutaSelectionExecutionResult:
    dataset_name: str
    outcome_variable: str
    predictor_variables: list[str]
    family: Literal['gaussian', 'binomial']
    event_level: str | None
    reference_level: str | None
    sample_size: int
    excluded_rows: int
    max_runs: int
    actual_runs: int
    selected_predictors: list[str]
    confirmed_count: int
    rejected_count: int
    tentative_count: int
    features: list[BorutaFeatureData]
    plots: list[LassoPlotData]
    note: str
    script_r: str


@dataclass
class BinaryModelMetricData:
    dataset: str
    sample_size: int
    event_count: int
    auc: float | None
    accuracy: float | None
    sensitivity: float | None
    specificity: float | None
    precision: float | None
    npv: float | None
    f1: float | None
    brier_score: float | None
    hosmer_lemeshow_p_value: float | None = None


@dataclass
class RegressionModelMetricData:
    dataset: str
    sample_size: int
    rmse: float | None
    mae: float | None
    r_squared: float | None


@dataclass
class TreeModelImportanceData:
    predictor: str
    importance: float | None
    secondary_importance: float | None
    tertiary_importance: float | None
    importance_scaled: float | None
    rank: int


@dataclass
class TreeModelExecutionResult:
    dataset_name: str
    model_type: Literal['random_forest', 'xgboost']
    task_kind: Literal['classification', 'regression']
    outcome_variable: str
    predictor_variables: list[str]
    event_level: str
    reference_level: str
    sample_size: int
    excluded_rows: int
    seed: int
    metrics: list[BinaryModelMetricData]
    importance_rows: list[TreeModelImportanceData]
    note: str
    script_r: str
    plots: list[LassoPlotData]
    regression_metrics: list[RegressionModelMetricData] = field(default_factory=list)
    trees: int | None = None
    mtry: int | None = None
    oob_error_rate: float | None = None
    eta: float | None = None
    max_depth: int | None = None
    nrounds: int | None = None


@dataclass
class RocValidationExecutionResult:
    dataset_name: str
    model_type: str
    evaluation_dataset: str
    auc: float | None
    auc_ci_low: float | None
    auc_ci_mid: float | None
    auc_ci_high: float | None
    threshold: float | None
    threshold_rule: str
    sample_size: int
    event_count: int
    accuracy: float | None
    sensitivity: float | None
    specificity: float | None
    precision: float | None
    npv: float | None
    f1: float | None
    brier_score: float | None
    note: str
    script_r: str
    plots: list[LassoPlotData]
    train_auc: float | None = None
    train_auc_ci_low: float | None = None
    train_auc_ci_high: float | None = None
    train_youden_index: float | None = None
    train_threshold: float | None = None
    train_sample_size: int = 0
    train_event_count: int = 0
    train_accuracy: float | None = None
    train_sensitivity: float | None = None
    train_specificity: float | None = None
    train_precision: float | None = None
    train_npv: float | None = None
    train_f1: float | None = None
    train_brier_score: float | None = None
    test_auc: float | None = None
    test_auc_ci_low: float | None = None
    test_auc_ci_high: float | None = None
    test_youden_index: float | None = None
    test_threshold: float | None = None
    test_sample_size: int = 0
    test_event_count: int = 0
    test_accuracy: float | None = None
    test_sensitivity: float | None = None
    test_specificity: float | None = None
    test_precision: float | None = None
    test_npv: float | None = None
    test_f1: float | None = None
    test_brier_score: float | None = None


@dataclass
class CalibrationMetricsData:
    c_index: float | None
    dxy: float | None
    intercept: float | None
    slope: float | None
    emax: float | None
    eavg: float | None
    brier: float | None
    r2: float | None


@dataclass
class CalibrationValidationExecutionResult:
    dataset_name: str
    model_type: str
    has_test: bool
    train_metrics: CalibrationMetricsData
    test_metrics: CalibrationMetricsData | None
    note: str
    script_r: str
    plots: list[LassoPlotData]


@dataclass
class DcaValidationRowData:
    threshold: float | None
    model_net_benefit: float | None
    treat_all_net_benefit: float | None
    treat_none_net_benefit: float | None


@dataclass
class DcaValidationExecutionResult:
    dataset_name: str
    model_type: str
    has_test: bool
    threshold_min: float | None
    threshold_max: float | None
    threshold_step: float | None
    train_dca_rows: list[DcaValidationRowData]
    test_dca_rows: list[DcaValidationRowData] | None
    note: str
    script_r: str
    plots: list[LassoPlotData]


@dataclass
class NomogramMetricsData:
    sample_size: int | None = None
    event_count: int | None = None
    auc: float | None = None
    brier_score: float | None = None
    concordance: float | None = None


@dataclass
class NomogramExecutionResult:
    dataset_name: str
    model_type: str
    has_test: bool
    scale_points: int
    timepoint: float | None
    train_metrics: NomogramMetricsData
    test_metrics: NomogramMetricsData | None
    note: str
    script_r: str
    plots: list[LassoPlotData]


@dataclass
class BootstrapValidationExecutionResult:
    dataset_name: str
    model_type: str
    metric_label: str
    requested_resamples: int
    completed_resamples: int
    seed: int
    apparent_metric: float | None
    mean_optimism: float | None
    optimism_corrected_metric: float | None
    summary_rows: list[list[object]]
    note: str
    script_r: str
    plots: list[LassoPlotData]


@dataclass
class CoxRegressionCoefficientData:
    term: str
    coefficient: float | None
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
    univariate_coefficients: list[CoxRegressionCoefficientData]
    coefficients: list[CoxRegressionCoefficientData]
    proportional_hazards_tests: list[CoxRegressionPhTestData]
    note: str
    script_r: str
    plots: list[LassoPlotData] = field(default_factory=list)


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


def _encode_plot(path: Path, name: str, vector_pdf_path: Path | None = None) -> LassoPlotData:
    return LassoPlotData(
        name=name,
        filename=path.name,
        media_type='image/png',
        content_base64=base64.b64encode(path.read_bytes()).decode('ascii'),
        vector_pdf_filename=vector_pdf_path.name if vector_pdf_path and vector_pdf_path.exists() else None,
        vector_pdf_base64=base64.b64encode(vector_pdf_path.read_bytes()).decode('ascii')
        if vector_pdf_path and vector_pdf_path.exists()
        else None,
    )


def _is_integer_like_numeric(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors='coerce').dropna()
    if numeric.empty:
        return False
    return bool(((numeric - numeric.round()).abs() < 1e-9).all())


def _json_arg(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalize_str_list(values: list[str] | None) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values or []:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _payload_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple, set)):
        return _normalize_str_list([str(item) for item in value])
    text = str(value).strip()
    return [text] if text else []


def _payload_metric_rows(value: object) -> list[BinaryModelMetricData]:
    rows: list[BinaryModelMetricData] = []
    if not isinstance(value, list):
        return rows
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) < 11:
            continue
        rows.append(
            BinaryModelMetricData(
                dataset=str(row[0]),
                sample_size=_to_int(row[1]),
                event_count=_to_int(row[2]),
                auc=_to_float(row[3]),
                accuracy=_to_float(row[4]),
                sensitivity=_to_float(row[5]),
                specificity=_to_float(row[6]),
                precision=_to_float(row[7]),
                npv=_to_float(row[8]),
                f1=_to_float(row[9]),
                brier_score=_to_float(row[10]),
                hosmer_lemeshow_p_value=_to_float(row[11]) if len(row) > 11 else None,
            )
        )
    return rows


def _payload_regression_metric_rows(value: object) -> list[RegressionModelMetricData]:
    rows: list[RegressionModelMetricData] = []
    if not isinstance(value, list):
        return rows
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        rows.append(
            RegressionModelMetricData(
                dataset=str(row[0]),
                sample_size=_to_int(row[1]),
                rmse=_to_float(row[2]),
                mae=_to_float(row[3]),
                r_squared=_to_float(row[4]),
            )
        )
    return rows


def _run_regression_script(script_name: str, args: list[str], error_message: str) -> str:
    script_path = get_r_script_path(script_name)
    run_rscript([script_path.as_posix(), *args], error_message)
    return load_r_script(script_name)


def run_missing_value_processing(
    df: pd.DataFrame,
    dataset_name: str,
    analysis_columns: list[str],
    method: str,
    threshold: float,
    protected_columns: list[str] | None = None,
) -> MissingValueExecutionResult:
    if not analysis_columns:
        raise BadRequest("缺失值处理至少需要一个分析字段")

    _sanitize_columns(df, analysis_columns)
    protected = _normalize_str_list(protected_columns)
    prepared = df.copy()
    for column in prepared.columns:
        if prepared[column].dtype == object:
            prepared[column] = prepared[column].map(lambda value: value.strip() if isinstance(value, str) else value)
            prepared[column] = prepared[column].replace('', pd.NA)

    normalized_method = str(method or "多重插补").strip()
    if normalized_method not in {"删除缺失", "均值/众数插补", "多重插补"}:
        raise BadRequest("不支持的缺失值处理方式")

    threshold_value = float(threshold)
    if threshold_value < 0 or threshold_value > 1:
        raise BadRequest("缺失比例阈值必须介于 0 和 1 之间")

    with tempfile.TemporaryDirectory(prefix='medicode-missing-value-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'missing_value_input.csv')
        output_csv_path = temp_path / 'missing_value_output.csv'
        output_json_path = temp_path / 'missing_value_output.json'
        script_r = _run_regression_script(
            'missing_value_processing.R',
            [
                csv_path.as_posix(),
                output_csv_path.as_posix(),
                output_json_path.as_posix(),
                dataset_name,
                normalized_method,
                str(threshold_value),
                _json_arg(analysis_columns),
                _json_arg(protected),
            ],
            '执行缺失值处理失败',
        )
        payload = _read_json(output_json_path)
        csv_content = output_csv_path.read_bytes()
        cleaned_df = load_tabular_dataframe(csv_content, '.csv')

    return MissingValueExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        method=str(payload.get('method') or normalized_method),
        threshold=_to_float(payload.get('threshold')) or threshold_value,
        input_rows=_to_int(payload.get('input_rows')),
        input_columns=_to_int(payload.get('input_columns')),
        output_rows=_to_int(payload.get('output_rows')),
        output_columns=_to_int(payload.get('output_columns')),
        removed_rows=_to_int(payload.get('removed_rows')),
        removed_columns=_to_int(payload.get('removed_columns')),
        removed_column_names=_payload_str_list(payload.get('removed_column_names')),
        numeric_imputed_cells=_to_int(payload.get('numeric_imputed_cells')),
        categorical_imputed_cells=_to_int(payload.get('categorical_imputed_cells')),
        missing_cells_before=_to_int(payload.get('missing_cells_before')),
        missing_cells_after=_to_int(payload.get('missing_cells_after')),
        processed_columns=_payload_str_list(payload.get('processed_columns')),
        output_name=str(payload.get('output_name') or f"{Path(dataset_name).stem}_missing_processed.csv"),
        operations=_payload_str_list(payload.get('operations')),
        cleaned_df=cleaned_df,
        csv_content=csv_content,
        script_r=script_r,
    )


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
        residual_plot_path = temp_path / 'linear_regression_residual_plot.png'
        residual_plot_pdf_path = temp_path / 'linear_regression_residual_plot.pdf'
        fitted_plot_path = temp_path / 'linear_regression_fitted_plot.png'
        fitted_plot_pdf_path = temp_path / 'linear_regression_fitted_plot.pdf'
        script = _run_regression_script(
            'linear_regression.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                residual_plot_path.as_posix(),
                residual_plot_pdf_path.as_posix(),
                fitted_plot_path.as_posix(),
                fitted_plot_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(alpha),
            ],
            'R 线性回归执行失败',
        )
        payload = _read_json(output_path)
        plots: list[LassoPlotData] = []
        if residual_plot_path.exists():
            plots.append(_encode_plot(residual_plot_path, '残差诊断图', residual_plot_pdf_path))
        if fitted_plot_path.exists():
            plots.append(_encode_plot(fitted_plot_path, '拟合值与观测值', fitted_plot_pdf_path))

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
        residual_normality_method=str(payload.get('residual_normality_method') or ''),
        residual_normality_p_value=_to_float(payload.get('residual_normality_p_value')),
        residual_normality_passed=bool(payload.get('residual_normality_passed', False)),
        homoscedasticity_test_method=str(payload.get('homoscedasticity_test_method') or ''),
        homoscedasticity_p_value=_to_float(payload.get('homoscedasticity_p_value')),
        homoscedasticity_passed=bool(payload.get('homoscedasticity_passed', False)),
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
        plots=plots,
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_logistic_regression(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    alpha: float,
    apply_univariate_screening: bool = True,
    screening_threshold: float = 0.1,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> LogisticRegressionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于 Logistic 回归')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, columns)
        prepared_test = _clean_dataframe(test_df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-logistic-regression-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'logistic_regression.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'logistic_regression_test.csv').as_posix()
        output_path = temp_path / 'logistic_regression_output.json'
        plot_forest_path = temp_path / 'logistic_regression_forest.png'
        plot_forest_pdf_path = temp_path / 'logistic_regression_forest.pdf'
        script = _run_regression_script(
            'logistic_regression.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                plot_forest_path.as_posix(),
                plot_forest_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(alpha),
                'internal' if apply_univariate_screening else 'respect_input',
                str(screening_threshold),
                test_csv_arg,
            ],
            'R Logistic 回归执行失败',
        )
        payload = _read_json(output_path)
        plots = []
        if plot_forest_path.exists():
            plots.append(_encode_plot(plot_forest_path, '森林图', plot_forest_pdf_path))

    return LogisticRegressionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        event_level=str(payload.get('event_level') or ''),
        reference_level=str(payload.get('reference_level') or ''),
        predictor_variables=_payload_str_list(payload.get('predictor_variables')) or predictor_variables,
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
        univariate_coefficients=[
            LogisticRegressionCoefficientData(
                term=str(row.get('term') or ''),
                coefficient=_to_float(row.get('coefficient')),
                odds_ratio=_to_float(row.get('odds_ratio')),
                std_error=_to_float(row.get('std_error')),
                z_value=_to_float(row.get('z_value')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
            )
            for row in (payload.get('univariate_coefficients') or [])
        ],
        coefficients=[
            LogisticRegressionCoefficientData(
                term=str(row.get('term') or ''),
                coefficient=_to_float(row.get('coefficient')),
                odds_ratio=_to_float(row.get('odds_ratio')),
                std_error=_to_float(row.get('std_error')),
                z_value=_to_float(row.get('z_value')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
            )
            for row in (payload.get('coefficients') or [])
        ],
        metrics=_payload_metric_rows(payload.get('metrics_rows')),
        hosmer_lemeshow_p_value=_to_float(payload.get('hosmer_lemeshow_p_value')),
        plots=plots,
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_univariate_logistic_screen(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    threshold: float | None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> UnivariateScreenExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于单因素 Logistic 筛选')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)
    selection_mode = 'display_only' if threshold is None else 'threshold'

    with tempfile.TemporaryDirectory(prefix='medicode-univariate-logistic-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'univariate_logistic.csv')
        output_path = temp_path / 'univariate_logistic_output.json'
        script = _run_regression_script(
            'univariate_logistic.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(threshold) if threshold is not None else 'NA',
                selection_mode,
            ],
            'R 单因素 Logistic 筛选执行失败',
        )
        payload = _read_json(output_path)

    return UnivariateScreenExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        analysis_kind='logistic',
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        time_variable=None,
        event_variable=None,
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        selection_mode=str(payload.get('selection_mode') or selection_mode),  # type: ignore[arg-type]
        threshold=_to_float(payload.get('threshold')),
        effect_label='OR',
        selected_predictors=[str(item) for item in (payload.get('selected_predictors') or predictor_variables)],
        coefficients=[
            UnivariateScreenCoefficientData(
                predictor=str(row.get('predictor') or ''),
                term=str(row.get('term') or ''),
                coefficient=_to_float(row.get('coefficient')),
                effect_value=_to_float(row.get('effect_value')),
                std_error=_to_float(row.get('std_error')),
                statistic=_to_float(row.get('statistic')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
                selected=bool(row.get('selected', False)),
            )
            for row in (payload.get('coefficients') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_univariate_linear_screen(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    threshold: float | None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> UnivariateScreenExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于单因素线性筛选')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    selection_mode = 'display_only' if threshold is None else 'threshold'
    categorical_predictors = set(_resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides))
    coefficients: list[UnivariateScreenCoefficientData] = []
    selected_predictors: list[str] = []
    sample_sizes: list[int] = []
    excluded_rows_by_predictor: list[int] = []

    outcome_numeric_full = pd.to_numeric(prepared[outcome_variable], errors='coerce')
    if outcome_numeric_full.dropna().empty:
        raise BadRequest('连续结局的单因素筛选要求结局变量可转换为数值型')

    for predictor in predictor_variables:
        subset = prepared[[outcome_variable, predictor]].copy()
        subset[outcome_variable] = pd.to_numeric(subset[outcome_variable], errors='coerce')
        subset = subset.dropna(axis=0, how='any')
        if subset.empty:
            continue

        y = subset[outcome_variable].astype(float).to_numpy()
        sample_sizes.append(int(subset.shape[0]))
        excluded_rows_by_predictor.append(int(prepared.shape[0] - subset.shape[0]))

        predictor_selected = False
        if predictor in categorical_predictors:
            encoded = pd.get_dummies(
                subset[predictor],
                prefix=predictor,
                prefix_sep='__',
                drop_first=True,
                dummy_na=False,
                dtype=int,
            ).astype(float)
            if encoded.empty:
                continue
            term_names = encoded.columns.tolist()
            x = encoded.to_numpy(dtype=float)
        else:
            numeric_predictor = pd.to_numeric(subset[predictor], errors='coerce')
            valid_mask = ~numeric_predictor.isna()
            if not bool(valid_mask.all()):
                y = y[valid_mask.to_numpy()]
                numeric_predictor = numeric_predictor[valid_mask]
            if numeric_predictor.dropna().nunique(dropna=True) <= 1:
                continue
            term_names = [predictor]
            x = numeric_predictor.to_numpy(dtype=float).reshape(-1, 1)

        design = np.column_stack([np.ones(x.shape[0]), x])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        fitted = design @ beta
        residuals = y - fitted
        dof = max(design.shape[0] - design.shape[1], 0)
        if dof <= 0:
            continue

        sse = float(np.square(residuals).sum())
        sigma2 = sse / dof
        xtx_inv = np.linalg.pinv(design.T @ design)
        standard_errors = np.sqrt(np.clip(np.diag(xtx_inv) * sigma2, a_min=0.0, a_max=None))
        critical = float(stats.t.ppf(0.975, dof))

        for index, term_name in enumerate(term_names, start=1):
            coefficient = float(beta[index])
            std_error = float(standard_errors[index]) if index < len(standard_errors) else None
            statistic = coefficient / std_error if std_error and std_error > 0 else None
            p_value = float(2 * stats.t.sf(abs(statistic), dof)) if statistic is not None else None
            conf_low = coefficient - critical * std_error if std_error is not None else None
            conf_high = coefficient + critical * std_error if std_error is not None else None
            selected = bool(threshold is not None and p_value is not None and p_value < threshold)
            predictor_selected = predictor_selected or selected
            coefficients.append(
                UnivariateScreenCoefficientData(
                    predictor=predictor,
                    term=term_name,
                    coefficient=coefficient,
                    effect_value=coefficient,
                    std_error=std_error,
                    statistic=statistic,
                    p_value=p_value,
                    conf_low=conf_low,
                    conf_high=conf_high,
                    selected=selected,
                )
            )

        if threshold is None or predictor_selected:
            selected_predictors.append(predictor)

    if not coefficients:
        raise BadRequest('单因素线性筛选未生成有效结果，请检查结局变量和自变量是否具备足够变异')

    selected_predictors = _normalize_str_list(selected_predictors)
    excluded_rows = max(excluded_rows_by_predictor) if excluded_rows_by_predictor else 0
    sample_size = max(sample_sizes) if sample_sizes else 0
    threshold_text = f"P < {threshold:.2f}" if threshold is not None else '仅展示'
    note = f"已按连续结局执行单因素线性筛选，当前规则为 {threshold_text}。"

    return UnivariateScreenExecutionResult(
        dataset_name=dataset_name,
        analysis_kind='linear',
        outcome_variable=outcome_variable,
        time_variable=None,
        event_variable=None,
        sample_size=sample_size,
        excluded_rows=excluded_rows,
        selection_mode=selection_mode,  # type: ignore[arg-type]
        threshold=threshold,
        effect_label='Beta',
        selected_predictors=selected_predictors if threshold is not None else predictor_variables,
        coefficients=coefficients,
        note=note,
        script_r='python:univariate_linear_screen',
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
        plot_cv_pdf_path = temp_path / 'lasso_cv_curve.pdf'
        plot_coef_path = temp_path / 'lasso_coefficient_path.png'
        plot_coef_pdf_path = temp_path / 'lasso_coefficient_path.pdf'
        script = _run_regression_script(
            'lasso_regression.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                plot_cv_path.as_posix(),
                plot_cv_pdf_path.as_posix(),
                plot_coef_path.as_posix(),
                plot_coef_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(alpha),
                str(nfolds),
            ],
            'R LASSO 回归执行失败',
        )
        payload = _read_json(output_path)
        if not plot_cv_path.exists() or not plot_coef_path.exists():
            raise BadRequest('LASSO 图像生成失败')
        plots = [
            _encode_plot(plot_cv_path, '交叉验证曲线', plot_cv_pdf_path),
            _encode_plot(plot_coef_path, '系数路径图', plot_coef_pdf_path),
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


def run_random_forest_importance_selection(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    trees: int,
    top_n: int,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> RandomForestSelectionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于随机森林变量筛选')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    trees_value = int(trees)
    top_n_value = int(top_n)
    if trees_value < 100:
        raise BadRequest('随机森林树数量建议不低于 100')
    if top_n_value < 1:
        raise BadRequest('随机森林至少需要保留 1 个变量')

    with tempfile.TemporaryDirectory(prefix='medicode-rf-selection-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'rf_selection.csv')
        output_path = temp_path / 'rf_selection_output.json'
        plot_importance_path = temp_path / 'rf_importance_bar.png'
        plot_importance_pdf_path = temp_path / 'rf_importance_bar.pdf'
        plot_cumulative_path = temp_path / 'rf_importance_cumulative.png'
        plot_cumulative_pdf_path = temp_path / 'rf_importance_cumulative.pdf'
        script = _run_regression_script(
            'random_forest_selection.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                plot_importance_path.as_posix(),
                plot_importance_pdf_path.as_posix(),
                plot_cumulative_path.as_posix(),
                plot_cumulative_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(trees_value),
                str(top_n_value),
            ],
            'R 随机森林变量筛选执行失败',
        )
        payload = _read_json(output_path)
        plots: list[LassoPlotData] = []
        if plot_importance_path.exists():
            plots.append(_encode_plot(plot_importance_path, '变量重要度条形图', plot_importance_pdf_path))
        if plot_cumulative_path.exists():
            plots.append(_encode_plot(plot_cumulative_path, '累积重要度曲线', plot_cumulative_pdf_path))

    return RandomForestSelectionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        predictor_variables=_payload_str_list(payload.get('predictor_variables')) or predictor_variables,
        family=str(payload.get('family') or 'binomial'),
        event_level=str(payload.get('event_level')) if payload.get('event_level') is not None else None,
        reference_level=str(payload.get('reference_level')) if payload.get('reference_level') is not None else None,
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        trees=_to_int(payload.get('trees')) or trees_value,
        top_n=_to_int(payload.get('top_n')) or top_n_value,
        importance_metric=str(payload.get('importance_metric') or 'importance'),
        secondary_metric=str(payload.get('secondary_metric')) if payload.get('secondary_metric') is not None else None,
        selected_predictors=_payload_str_list(payload.get('selected_predictors')),
        importance_rows=[
            RandomForestImportanceFeatureData(
                predictor=str(row.get('predictor') or ''),
                importance=_to_float(row.get('importance')),
                secondary_importance=_to_float(row.get('secondary_importance')),
                normalized_importance=_to_float(row.get('normalized_importance')),
                rank=_to_int(row.get('rank')),
                selected=bool(row.get('selected', False)),
            )
            for row in (payload.get('importance_rows') or [])
        ],
        plots=plots,
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_boruta_selection(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    max_runs: int,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> BorutaSelectionExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于 Boruta 变量筛选')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)

    max_runs_value = int(max_runs)
    if max_runs_value < 20:
        raise BadRequest('Boruta 最大迭代次数建议不低于 20')

    with tempfile.TemporaryDirectory(prefix='medicode-boruta-selection-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'boruta_selection.csv')
        output_path = temp_path / 'boruta_selection_output.json'
        plot_history_path = temp_path / 'boruta_importance_history.png'
        plot_history_pdf_path = temp_path / 'boruta_importance_history.pdf'
        plot_decision_path = temp_path / 'boruta_decision_summary.png'
        plot_decision_pdf_path = temp_path / 'boruta_decision_summary.pdf'
        script = _run_regression_script(
            'boruta_selection.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                plot_history_path.as_posix(),
                plot_history_pdf_path.as_posix(),
                plot_decision_path.as_posix(),
                plot_decision_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(max_runs_value),
            ],
            'R Boruta 变量筛选执行失败',
        )
        payload = _read_json(output_path)
        plots: list[LassoPlotData] = []
        if plot_history_path.exists():
            plots.append(_encode_plot(plot_history_path, 'Boruta 重要度历史图', plot_history_pdf_path))
        if plot_decision_path.exists():
            plots.append(_encode_plot(plot_decision_path, 'Boruta 决策汇总图', plot_decision_pdf_path))

    return BorutaSelectionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        predictor_variables=_payload_str_list(payload.get('predictor_variables')) or predictor_variables,
        family=str(payload.get('family') or 'binomial'),
        event_level=str(payload.get('event_level')) if payload.get('event_level') is not None else None,
        reference_level=str(payload.get('reference_level')) if payload.get('reference_level') is not None else None,
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        max_runs=_to_int(payload.get('max_runs')) or max_runs_value,
        actual_runs=_to_int(payload.get('actual_runs')),
        selected_predictors=_payload_str_list(payload.get('selected_predictors')),
        confirmed_count=_to_int(payload.get('confirmed_count')),
        rejected_count=_to_int(payload.get('rejected_count')),
        tentative_count=_to_int(payload.get('tentative_count')),
        features=[
            BorutaFeatureData(
                predictor=str(row.get('predictor') or ''),
                decision=str(row.get('decision') or ''),
                mean_importance=_to_float(row.get('mean_importance')),
                median_importance=_to_float(row.get('median_importance')),
                min_importance=_to_float(row.get('min_importance')),
                max_importance=_to_float(row.get('max_importance')),
                normalized_hits=_to_float(row.get('normalized_hits')),
                selected=bool(row.get('selected', False)),
            )
            for row in (payload.get('features') or [])
        ],
        plots=plots,
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_random_forest_model(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    trees: int,
    mtry: str,
    seed: int,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> TreeModelExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于随机森林建模')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, columns)
        prepared_test = _clean_dataframe(test_df, columns)

    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)
    trees_value = int(trees)
    seed_value = int(seed)
    if trees_value < 100:
        raise BadRequest('随机森林树数量建议不低于 100')

    with tempfile.TemporaryDirectory(prefix='medicode-rf-model-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared, temp_path, 'rf_model_train.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'rf_model_test.csv').as_posix()
        output_path = temp_path / 'rf_model_output.json'
        plot_roc_path = temp_path / 'rf_model_roc.png'
        plot_roc_pdf_path = temp_path / 'rf_model_roc.pdf'
        plot_importance_path = temp_path / 'rf_model_importance.png'
        plot_importance_pdf_path = temp_path / 'rf_model_importance.pdf'
        script = _run_regression_script(
            'random_forest_model.R',
            [
                train_csv_path.as_posix(),
                test_csv_arg,
                output_path.as_posix(),
                plot_roc_path.as_posix(),
                plot_roc_pdf_path.as_posix(),
                plot_importance_path.as_posix(),
                plot_importance_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(trees_value),
                str(mtry),
                str(seed_value),
            ],
            'R 随机森林建模执行失败',
        )
        payload = _read_json(output_path)
        task_kind = str(payload.get("task_kind") or "classification")
        plots: list[LassoPlotData] = []
        if plot_roc_path.exists():
            plots.append(_encode_plot(plot_roc_path, 'ROC 曲线' if task_kind == "classification" else '预测 vs 实际', plot_roc_pdf_path))
        if plot_importance_path.exists():
            plots.append(_encode_plot(plot_importance_path, '变量重要度图', plot_importance_pdf_path))

    task_kind = str(payload.get("task_kind") or "classification")
    metrics = _payload_metric_rows(payload.get("metrics_rows")) if task_kind == "classification" else []
    regression_metrics = _payload_regression_metric_rows(payload.get("regression_metrics_rows")) if task_kind == "regression" else []

    return TreeModelExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type='random_forest',
        task_kind="regression" if task_kind == "regression" else "classification",
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        predictor_variables=_payload_str_list(payload.get('predictor_variables')) or predictor_variables,
        event_level=str(payload.get('event_level') or ''),
        reference_level=str(payload.get('reference_level') or ''),
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        seed=_to_int(payload.get('seed')) or seed_value,
        metrics=metrics,
        importance_rows=[
            TreeModelImportanceData(
                predictor=str(row.get('predictor') or ''),
                importance=_to_float(row.get('importance')),
                secondary_importance=_to_float(row.get('secondary_importance')),
                tertiary_importance=None,
                importance_scaled=_to_float(row.get('importance_scaled')),
                rank=_to_int(row.get('rank')),
            )
            for row in (payload.get('importance_rows') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
        regression_metrics=regression_metrics,
        trees=_to_int(payload.get('trees')) or trees_value,
        mtry=_to_int(payload.get('mtry')),
        oob_error_rate=_to_float(payload.get('oob_error_rate')),
    )


def run_xgboost_model(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_variable: str,
    predictor_variables: list[str],
    eta: float,
    depth: int,
    rounds: int,
    seed: int,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> TreeModelExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于 XGBoost 建模')

    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, columns)
        prepared_test = _clean_dataframe(test_df, columns)

    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)
    eta_value = float(eta)
    depth_value = int(depth)
    rounds_value = int(rounds)
    seed_value = int(seed)
    if eta_value <= 0 or eta_value >= 1:
        raise BadRequest('XGBoost 学习率 eta 需介于 0 和 1 之间')
    if depth_value < 1:
        raise BadRequest('XGBoost max_depth 至少为 1')
    if rounds_value < 10:
        raise BadRequest('XGBoost nrounds 建议不低于 10')

    with tempfile.TemporaryDirectory(prefix='medicode-xgb-model-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared, temp_path, 'xgb_model_train.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'xgb_model_test.csv').as_posix()
        output_path = temp_path / 'xgb_model_output.json'
        plot_roc_path = temp_path / 'xgb_model_roc.png'
        plot_roc_pdf_path = temp_path / 'xgb_model_roc.pdf'
        plot_importance_path = temp_path / 'xgb_model_importance.png'
        plot_importance_pdf_path = temp_path / 'xgb_model_importance.pdf'
        script = _run_regression_script(
            'xgboost_model.R',
            [
                train_csv_path.as_posix(),
                test_csv_arg,
                output_path.as_posix(),
                plot_roc_path.as_posix(),
                plot_roc_pdf_path.as_posix(),
                plot_importance_path.as_posix(),
                plot_importance_pdf_path.as_posix(),
                dataset_name,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(eta_value),
                str(depth_value),
                str(rounds_value),
                str(seed_value),
            ],
            'R XGBoost 建模执行失败',
        )
        payload = _read_json(output_path)
        task_kind = str(payload.get("task_kind") or "classification")
        plots: list[LassoPlotData] = []
        if plot_roc_path.exists():
            plots.append(_encode_plot(plot_roc_path, 'ROC 曲线' if task_kind == "classification" else '预测 vs 实际', plot_roc_pdf_path))
        if plot_importance_path.exists():
            plots.append(_encode_plot(plot_importance_path, '变量重要度图', plot_importance_pdf_path))

    task_kind = str(payload.get("task_kind") or "classification")
    metrics = _payload_metric_rows(payload.get("metrics_rows")) if task_kind == "classification" else []
    regression_metrics = _payload_regression_metric_rows(payload.get("regression_metrics_rows")) if task_kind == "regression" else []

    return TreeModelExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type='xgboost',
        task_kind="regression" if task_kind == "regression" else "classification",
        outcome_variable=str(payload.get('outcome_variable') or outcome_variable),
        predictor_variables=_payload_str_list(payload.get('predictor_variables')) or predictor_variables,
        event_level=str(payload.get('event_level') or ''),
        reference_level=str(payload.get('reference_level') or ''),
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        seed=_to_int(payload.get('seed')) or seed_value,
        metrics=metrics,
        importance_rows=[
            TreeModelImportanceData(
                predictor=str(row.get('predictor') or ''),
                importance=_to_float(row.get('importance')),
                secondary_importance=_to_float(row.get('secondary_importance')),
                tertiary_importance=_to_float(row.get('tertiary_importance')),
                importance_scaled=_to_float(row.get('importance_scaled')),
                rank=_to_int(row.get('rank')),
            )
            for row in (payload.get('importance_rows') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
        regression_metrics=regression_metrics,
        eta=_to_float(payload.get('eta')) or eta_value,
        max_depth=_to_int(payload.get('max_depth')) or depth_value,
        nrounds=_to_int(payload.get('nrounds')) or rounds_value,
    )


def run_roc_validation(
    train_df: pd.DataFrame,
    dataset_name: str,
    model_type: str,
    outcome_variable: str,
    predictor_variables: list[str],
    ci_mode: str,
    cutoff_rule: str,
    model_params: dict[str, object] | None = None,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> RocValidationExecutionResult:
    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(train_df, columns)
    prepared_train = _clean_dataframe(train_df, columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, columns)
        prepared_test = _clean_dataframe(test_df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared_train, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-roc-validation-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared_train, temp_path, 'roc_train.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'roc_test.csv').as_posix()
        output_path = temp_path / 'roc_output.json'
        plot_path = temp_path / 'roc_curve.png'
        plot_pdf_path = temp_path / 'roc_curve.pdf'
        script = _run_regression_script(
            'roc_validation.R',
            [
                train_csv_path.as_posix(),
                test_csv_arg,
                output_path.as_posix(),
                plot_path.as_posix(),
                plot_pdf_path.as_posix(),
                dataset_name,
                model_type,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                _json_arg(model_params or {}),
                ci_mode,
                cutoff_rule,
            ],
            'R ROC / AUC 验证执行失败',
        )
        payload = _read_json(output_path)
        plots = [_encode_plot(plot_path, 'ROC 曲线', plot_pdf_path)] if plot_path.exists() else []

    return RocValidationExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type=str(payload.get('model_type') or model_type),
        evaluation_dataset=str(payload.get('evaluation_dataset') or '训练集'),
        auc=_to_float(payload.get('auc')),
        auc_ci_low=_to_float(payload.get('auc_ci_low')),
        auc_ci_mid=_to_float(payload.get('auc_ci_mid')),
        auc_ci_high=_to_float(payload.get('auc_ci_high')),
        threshold=_to_float(payload.get('threshold')),
        threshold_rule=str(payload.get('threshold_rule') or cutoff_rule),
        sample_size=_to_int(payload.get('sample_size')),
        event_count=_to_int(payload.get('event_count')),
        accuracy=_to_float(payload.get('accuracy')),
        sensitivity=_to_float(payload.get('sensitivity')),
        specificity=_to_float(payload.get('specificity')),
        precision=_to_float(payload.get('precision')),
        npv=_to_float(payload.get('npv')),
        f1=_to_float(payload.get('f1')),
        brier_score=_to_float(payload.get('brier_score')),
        train_auc=_to_float(payload.get('train_auc')),
        train_auc_ci_low=_to_float(payload.get('train_auc_ci_low')),
        train_auc_ci_high=_to_float(payload.get('train_auc_ci_high')),
        train_youden_index=_to_float(payload.get('train_youden_index')),
        train_threshold=_to_float(payload.get('train_optimal_threshold')),
        train_sample_size=_to_int(payload.get('train_sample_size')),
        train_event_count=_to_int(payload.get('train_event_count')),
        train_accuracy=_to_float(payload.get('train_accuracy')),
        train_sensitivity=_to_float(payload.get('train_sensitivity')),
        train_specificity=_to_float(payload.get('train_specificity')),
        train_precision=_to_float(payload.get('train_precision')),
        train_npv=_to_float(payload.get('train_npv')),
        train_f1=_to_float(payload.get('train_f1')),
        train_brier_score=_to_float(payload.get('train_brier_score')),
        test_auc=_to_float(payload.get('test_auc')),
        test_auc_ci_low=_to_float(payload.get('test_auc_ci_low')),
        test_auc_ci_high=_to_float(payload.get('test_auc_ci_high')),
        test_youden_index=_to_float(payload.get('test_youden_index')),
        test_threshold=_to_float(payload.get('test_optimal_threshold')),
        test_sample_size=_to_int(payload.get('test_sample_size')),
        test_event_count=_to_int(payload.get('test_event_count')),
        test_accuracy=_to_float(payload.get('test_accuracy')),
        test_sensitivity=_to_float(payload.get('test_sensitivity')),
        test_specificity=_to_float(payload.get('test_specificity')),
        test_precision=_to_float(payload.get('test_precision')),
        test_npv=_to_float(payload.get('test_npv')),
        test_f1=_to_float(payload.get('test_f1')),
        test_brier_score=_to_float(payload.get('test_brier_score')),
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
    )


def run_calibration_validation(
    train_df: pd.DataFrame,
    dataset_name: str,
    model_type: str,
    outcome_variable: str,
    predictor_variables: list[str],
    bins_mode: str,
    resamples: int,
    model_params: dict[str, object] | None = None,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> CalibrationValidationExecutionResult:
    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(train_df, columns)
    prepared_train = _clean_dataframe(train_df, columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, columns)
        prepared_test = _clean_dataframe(test_df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared_train, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-calibration-validation-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared_train, temp_path, 'calibration_train.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'calibration_test.csv').as_posix()
        output_path = temp_path / 'calibration_output.json'
        train_plot_path = temp_path / 'calibration_train.png'
        train_plot_pdf_path = temp_path / 'calibration_train.pdf'
        test_plot_path = temp_path / 'calibration_test.png'
        test_plot_pdf_path = temp_path / 'calibration_test.pdf'
        script = _run_regression_script(
            'calibration_validation.R',
            [
                train_csv_path.as_posix(),
                test_csv_arg,
                output_path.as_posix(),
                train_plot_path.as_posix(),
                train_plot_pdf_path.as_posix(),
                test_plot_path.as_posix(),
                test_plot_pdf_path.as_posix(),
                dataset_name,
                model_type,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                _json_arg(model_params or {}),
            ],
            'R 校准曲线验证执行失败',
        )
        payload = _read_json(output_path)
        plots: list[LassoPlotData] = []
        if train_plot_path.exists():
            plots.append(_encode_plot(train_plot_path, '训练集校准曲线', train_plot_pdf_path))
        if payload.get('has_test') and test_plot_path.exists():
            plots.append(_encode_plot(test_plot_path, '测试集校准曲线', test_plot_pdf_path))

    def _parse_cal_metrics(d: dict | None) -> CalibrationMetricsData:
        if not d:
            return CalibrationMetricsData(None, None, None, None, None, None, None, None)
        return CalibrationMetricsData(
            c_index=_to_float(d.get('c_index')),
            dxy=_to_float(d.get('dxy')),
            intercept=_to_float(d.get('intercept')),
            slope=_to_float(d.get('slope')),
            emax=_to_float(d.get('emax')),
            eavg=_to_float(d.get('eavg')),
            brier=_to_float(d.get('brier')),
            r2=_to_float(d.get('r2')),
        )

    has_test = bool(payload.get('has_test'))
    return CalibrationValidationExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type=str(payload.get('model_type') or model_type),
        has_test=has_test,
        train_metrics=_parse_cal_metrics(payload.get('train_metrics')),
        test_metrics=_parse_cal_metrics(payload.get('test_metrics')) if has_test else None,
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
    )


def run_dca_validation(
    train_df: pd.DataFrame,
    dataset_name: str,
    model_type: str,
    outcome_variable: str,
    predictor_variables: list[str],
    range_text: str,
    step: float,
    model_params: dict[str, object] | None = None,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> DcaValidationExecutionResult:
    columns = [outcome_variable, *predictor_variables]
    _sanitize_columns(train_df, columns)
    prepared_train = _clean_dataframe(train_df, columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, columns)
        prepared_test = _clean_dataframe(test_df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared_train, predictor_variables, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-dca-validation-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared_train, temp_path, 'dca_train.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'dca_test.csv').as_posix()
        output_path = temp_path / 'dca_output.json'
        train_plot_path = temp_path / 'dca_curve_train.png'
        train_plot_pdf_path = temp_path / 'dca_curve_train.pdf'
        test_plot_path = temp_path / 'dca_curve_test.png'
        test_plot_pdf_path = temp_path / 'dca_curve_test.pdf'
        script = _run_regression_script(
            'dca_validation.R',
            [
                train_csv_path.as_posix(),
                test_csv_arg,
                output_path.as_posix(),
                train_plot_path.as_posix(),
                train_plot_pdf_path.as_posix(),
                test_plot_path.as_posix(),
                test_plot_pdf_path.as_posix(),
                dataset_name,
                model_type,
                outcome_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                _json_arg(model_params or {}),
                range_text,
                str(float(step)),
            ],
            'R DCA 验证执行失败',
        )
        payload = _read_json(output_path)
        has_test = bool(payload.get('has_test'))
        plots: list[LassoPlotData] = []
        if train_plot_path.exists():
            plots.append(_encode_plot(train_plot_path, '训练集 DCA', train_plot_pdf_path))
        if has_test and test_plot_path.exists():
            plots.append(_encode_plot(test_plot_path, '测试集 DCA', test_plot_pdf_path))

        train_rows = payload.get('train_dca_rows') or payload.get('dca_rows') or []
        test_rows = payload.get('test_dca_rows') if has_test else None

    return DcaValidationExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type=str(payload.get('model_type') or model_type),
        has_test=bool(payload.get('has_test')),
        threshold_min=_to_float(payload.get('threshold_min')),
        threshold_max=_to_float(payload.get('threshold_max')),
        threshold_step=_to_float(payload.get('threshold_step')),
        train_dca_rows=[
            DcaValidationRowData(
                threshold=_to_float(row.get('threshold')),
                model_net_benefit=_to_float(row.get('model_net_benefit')),
                treat_all_net_benefit=_to_float(row.get('treat_all_net_benefit')),
                treat_none_net_benefit=_to_float(row.get('treat_none_net_benefit')),
            )
            for row in train_rows
        ],
        test_dca_rows=[
            DcaValidationRowData(
                threshold=_to_float(row.get('threshold')),
                model_net_benefit=_to_float(row.get('model_net_benefit')),
                treat_all_net_benefit=_to_float(row.get('treat_all_net_benefit')),
                treat_none_net_benefit=_to_float(row.get('treat_none_net_benefit')),
            )
            for row in (test_rows or [])
        ]
        if test_rows is not None
        else None,
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
    )


def run_nomogram_plot(
    train_df: pd.DataFrame,
    dataset_name: str,
    model_type: Literal["logistic", "cox"],
    predictor_variables: list[str],
    scale_points: int,
    timepoint_text: str | None = None,
    outcome_variable: str | None = None,
    time_variable: str | None = None,
    event_variable: str | None = None,
    model_params: dict[str, object] | None = None,
    test_df: pd.DataFrame | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> NomogramExecutionResult:
    normalized_predictors = _payload_str_list(predictor_variables)
    required_columns: list[str]
    if model_type == "logistic":
        if not outcome_variable:
            raise BadRequest("列线图缺少结局变量，无法生成。")
        required_columns = [outcome_variable, *normalized_predictors]
    else:
        if not time_variable or not event_variable:
            raise BadRequest("列线图缺少生存时间/事件变量，无法生成。")
        required_columns = [time_variable, event_variable, *normalized_predictors]

    _sanitize_columns(train_df, required_columns)
    prepared_train = _clean_dataframe(train_df, required_columns)
    prepared_test: pd.DataFrame | None = None
    if test_df is not None and not test_df.empty:
        _sanitize_columns(test_df, required_columns)
        prepared_test = _clean_dataframe(test_df, required_columns)
    categorical_predictors = _resolve_categorical_predictors(prepared_train, normalized_predictors, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-nomogram-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared_train, temp_path, 'nomogram_train.csv')
        test_csv_arg = 'NA'
        if prepared_test is not None:
            test_csv_arg = _write_dataframe(prepared_test, temp_path, 'nomogram_test.csv').as_posix()
        output_path = temp_path / 'nomogram_output.json'
        plot_path = temp_path / 'nomogram.png'
        plot_pdf_path = temp_path / 'nomogram.pdf'
        script = _run_regression_script(
            'nomogram_plot.R',
            [
                train_csv_path.as_posix(),
                test_csv_arg,
                output_path.as_posix(),
                plot_path.as_posix(),
                plot_pdf_path.as_posix(),
                dataset_name,
                model_type,
                outcome_variable or 'NA',
                time_variable or 'NA',
                event_variable or 'NA',
                _json_arg(normalized_predictors),
                _json_arg(categorical_predictors),
                _json_arg(model_params or {}),
                str(int(scale_points)),
                str(timepoint_text or ''),
            ],
            'R 列线图执行失败',
        )
        payload = _read_json(output_path)
        plots = [_encode_plot(plot_path, 'Nomogram', plot_pdf_path)] if plot_path.exists() else []

    def _parse_metrics(raw: object | None) -> NomogramMetricsData:
        if not isinstance(raw, dict):
            return NomogramMetricsData()
        return NomogramMetricsData(
            sample_size=_to_int(raw.get('sample_size')),
            event_count=_to_int(raw.get('event_count')),
            auc=_to_float(raw.get('auc')),
            brier_score=_to_float(raw.get('brier_score')),
            concordance=_to_float(raw.get('concordance')),
        )

    has_test = bool(payload.get('has_test'))
    return NomogramExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type=str(payload.get('model_type') or model_type),
        has_test=has_test,
        scale_points=int(payload.get('scale_points') or scale_points or 100),
        timepoint=_to_float(payload.get('timepoint')),
        train_metrics=_parse_metrics(payload.get('train_metrics')),
        test_metrics=_parse_metrics(payload.get('test_metrics')) if has_test else None,
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
    )


def run_bootstrap_validation(
    train_df: pd.DataFrame,
    dataset_name: str,
    model_type: str,
    predictor_variables: list[str],
    resamples: int,
    seed: int,
    outcome_variable: str | None = None,
    time_variable: str | None = None,
    event_variable: str | None = None,
    model_params: dict[str, object] | None = None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> BootstrapValidationExecutionResult:
    normalized_predictors = _payload_str_list(predictor_variables)
    required_columns = [item for item in [outcome_variable, time_variable, event_variable] if item] + normalized_predictors
    _sanitize_columns(train_df, required_columns)
    prepared_train = _clean_dataframe(train_df, required_columns)
    categorical_predictors = _resolve_categorical_predictors(prepared_train, normalized_predictors, predictor_kind_overrides)

    with tempfile.TemporaryDirectory(prefix='medicode-bootstrap-validation-') as temp_dir:
        temp_path = Path(temp_dir)
        train_csv_path = _write_dataframe(prepared_train, temp_path, 'bootstrap_train.csv')
        output_path = temp_path / 'bootstrap_output.json'
        plot_path = temp_path / 'bootstrap_histogram.png'
        plot_pdf_path = temp_path / 'bootstrap_histogram.pdf'
        script = _run_regression_script(
            'bootstrap_validation.R',
            [
                train_csv_path.as_posix(),
                output_path.as_posix(),
                plot_path.as_posix(),
                plot_pdf_path.as_posix(),
                dataset_name,
                model_type,
                outcome_variable or 'NA',
                time_variable or 'NA',
                event_variable or 'NA',
                _json_arg(normalized_predictors),
                _json_arg(categorical_predictors),
                _json_arg(model_params or {}),
                str(int(resamples)),
                str(int(seed)),
            ],
            'R Bootstrap 验证执行失败',
        )
        payload = _read_json(output_path)
        plots = [_encode_plot(plot_path, 'Bootstrap Optimism Distribution', plot_pdf_path)] if plot_path.exists() else []

    summary_rows: list[list[object]] = []
    for row in (payload.get('summary_rows') or []):
        if isinstance(row, dict):
            summary_rows.append([row.get('metric'), row.get('value')])

    return BootstrapValidationExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        model_type=str(payload.get('model_type') or model_type),
        metric_label=str(payload.get('metric_label') or 'Metric'),
        requested_resamples=_to_int(payload.get('requested_resamples')) or int(resamples),
        completed_resamples=_to_int(payload.get('completed_resamples')),
        seed=_to_int(payload.get('seed')) or int(seed),
        apparent_metric=_to_float(payload.get('apparent_metric')),
        mean_optimism=_to_float(payload.get('mean_optimism')),
        optimism_corrected_metric=_to_float(payload.get('optimism_corrected_metric')),
        summary_rows=summary_rows,
        note=str(payload.get('note') or ''),
        script_r=script,
        plots=plots,
    )


def run_cox_regression(
    df: pd.DataFrame,
    dataset_name: str,
    time_variable: str,
    event_variable: str,
    predictor_variables: list[str],
    alpha: float,
    apply_univariate_screening: bool = True,
    screening_threshold: float = 0.1,
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
        plot_forest_path = temp_path / 'cox_forest_plot.png'
        plot_forest_pdf_path = temp_path / 'cox_forest_plot.pdf'
        script = _run_regression_script(
            'cox_regression.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                plot_forest_path.as_posix(),
                plot_forest_pdf_path.as_posix(),
                dataset_name,
                time_variable,
                event_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(alpha),
                'internal' if apply_univariate_screening else 'respect_input',
                str(screening_threshold),
            ],
            'R Cox 生存分析执行失败',
        )
        payload = _read_json(output_path)
        
        plots = []
        if plot_forest_path.exists():
            plots.append(_encode_plot(plot_forest_path, '森林图', plot_forest_pdf_path))

    return CoxRegressionExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        time_variable=str(payload.get('time_variable') or time_variable),
        event_variable=str(payload.get('event_variable') or event_variable),
        event_level=str(payload.get('event_level') or ''),
        reference_level=str(payload.get('reference_level') or ''),
        predictor_variables=_payload_str_list(payload.get('predictor_variables')) or predictor_variables,
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
        univariate_coefficients=[
            CoxRegressionCoefficientData(
                term=str(row.get('term') or ''),
                coefficient=_to_float(row.get('coefficient')),
                hazard_ratio=_to_float(row.get('hazard_ratio')),
                std_error=_to_float(row.get('std_error')),
                z_value=_to_float(row.get('z_value')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
            )
            for row in (payload.get('univariate_coefficients') or [])
        ],
        coefficients=[
            CoxRegressionCoefficientData(
                term=str(row.get('term') or ''),
                coefficient=_to_float(row.get('coefficient')),
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
        plots=plots,
        note=str(payload.get('note') or ''),
        script_r=script,
    )


def run_univariate_cox_screen(
    df: pd.DataFrame,
    dataset_name: str,
    time_variable: str,
    event_variable: str,
    predictor_variables: list[str],
    threshold: float | None,
    predictor_kind_overrides: dict[str, str] | None = None,
) -> UnivariateScreenExecutionResult:
    if not predictor_variables:
        raise BadRequest('请至少选择一个自变量用于单因素 Cox 筛选')

    columns = [time_variable, event_variable, *predictor_variables]
    _sanitize_columns(df, columns)
    prepared = _clean_dataframe(df, columns)
    categorical_predictors = _resolve_categorical_predictors(prepared, predictor_variables, predictor_kind_overrides)
    selection_mode = 'display_only' if threshold is None else 'threshold'

    with tempfile.TemporaryDirectory(prefix='medicode-univariate-cox-') as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = _write_dataframe(prepared, temp_path, 'univariate_cox.csv')
        output_path = temp_path / 'univariate_cox_output.json'
        script = _run_regression_script(
            'univariate_cox.R',
            [
                csv_path.as_posix(),
                output_path.as_posix(),
                dataset_name,
                time_variable,
                event_variable,
                _json_arg(predictor_variables),
                _json_arg(categorical_predictors),
                str(threshold) if threshold is not None else 'NA',
                selection_mode,
            ],
            'R 单因素 Cox 筛选执行失败',
        )
        payload = _read_json(output_path)

    return UnivariateScreenExecutionResult(
        dataset_name=str(payload.get('dataset_name') or dataset_name),
        analysis_kind='cox',
        outcome_variable=None,
        time_variable=str(payload.get('time_variable') or time_variable),
        event_variable=str(payload.get('event_variable') or event_variable),
        sample_size=_to_int(payload.get('sample_size')),
        excluded_rows=_to_int(payload.get('excluded_rows')),
        selection_mode=str(payload.get('selection_mode') or selection_mode),  # type: ignore[arg-type]
        threshold=_to_float(payload.get('threshold')),
        effect_label='HR',
        selected_predictors=[str(item) for item in (payload.get('selected_predictors') or predictor_variables)],
        coefficients=[
            UnivariateScreenCoefficientData(
                predictor=str(row.get('predictor') or ''),
                term=str(row.get('term') or ''),
                coefficient=_to_float(row.get('coefficient')),
                effect_value=_to_float(row.get('effect_value')),
                std_error=_to_float(row.get('std_error')),
                statistic=_to_float(row.get('statistic')),
                p_value=_to_float(row.get('p_value')),
                conf_low=_to_float(row.get('conf_low')),
                conf_high=_to_float(row.get('conf_high')),
                selected=bool(row.get('selected', False)),
            )
            for row in (payload.get('coefficients') or [])
        ],
        note=str(payload.get('note') or ''),
        script_r=script,
    )
