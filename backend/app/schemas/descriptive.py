"""Schemas for descriptive statistics and Table 1 generation."""

from typing import Literal

from pydantic import BaseModel, Field


class TableOneRequest(BaseModel):
    dataset_id: str
    group_variable: str
    variables: list[str] = Field(default_factory=list)
    decimals: int = Field(default=1, ge=0, le=4)


class TableOneTablePayload(BaseModel):
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


class TableOneResponse(TableOneTablePayload):
    pass


class TableOneInterpretRequest(BaseModel):
    dataset_id: str
    language: Literal["zh", "en"] = "zh"
    table: TableOneTablePayload


class TableOneInterpretResponse(BaseModel):
    feature_name: str
    language: Literal["zh", "en"]
    model: str
    content: str
    analysis_id: str | None = None
    saved_at: str | None = None
    llm_tokens_used: int = 0
    charged_tokens: int = 0
    remaining_balance: int = 0


class SavedTableOneInterpretResponse(BaseModel):
    found: bool
    feature_name: str | None = None
    language: Literal["zh", "en"] | None = None
    model: str | None = None
    content: str | None = None
    analysis_id: str | None = None
    saved_at: str | None = None
    llm_tokens_used: int = 0
    charged_tokens: int = 0


class TTestRequest(BaseModel):
    dataset_id: str
    group_variable: str
    continuous_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)
    confirm_independence: bool = True


class TTestGroupSummary(BaseModel):
    group: str
    n: int
    mean: float | None = None
    sd: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None


class TTestNormalityCheck(BaseModel):
    group: str
    n: int
    p_value: float | None = None
    passed: bool = False
    method: str


class TTestVariableResult(BaseModel):
    variable: str
    group_summaries: list[TTestGroupSummary]
    normality_checks: list[TTestNormalityCheck]
    variance_test_name: str
    variance_p_value: float | None = None
    equal_variance: bool | None = None
    satisfies_t_test: bool = False
    recommended_test: str
    executed_test: str
    statistic: float | None = None
    df: float | None = None
    p_value: float | None = None
    estimate: float | None = None
    conf_low: float | None = None
    conf_high: float | None = None
    note: str


class TTestResponse(BaseModel):
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    alpha: float
    confirm_independence: bool
    assumptions: list[str]
    variables: list[TTestVariableResult]


class AnovaRequest(BaseModel):
    dataset_id: str
    group_variable: str
    continuous_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)
    confirm_independence: bool = True


class AnovaVariableResult(BaseModel):
    variable: str
    group_summaries: list[TTestGroupSummary]
    normality_checks: list[TTestNormalityCheck]
    variance_test_name: str
    variance_p_value: float | None = None
    equal_variance: bool | None = None
    satisfies_anova: bool = False
    recommended_test: str
    executed_test: str
    statistic: float | None = None
    df_between: float | None = None
    df_within: float | None = None
    p_value: float | None = None
    note: str


class AnovaResponse(BaseModel):
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    alpha: float
    confirm_independence: bool
    assumptions: list[str]
    variables: list[AnovaVariableResult]


class ChiSquareRequest(BaseModel):
    dataset_id: str
    group_variable: str
    categorical_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)
    confirm_independence: bool = True


class ChiSquareLevelRow(BaseModel):
    level: str
    group_values: list[str]


class ChiSquareVariableResult(BaseModel):
    variable: str
    level_rows: list[ChiSquareLevelRow]
    minimum_expected_count: float | None = None
    expected_count_warning: bool = False
    recommended_test: str
    executed_test: str
    statistic: float | None = None
    df: float | None = None
    p_value: float | None = None
    note: str


class ChiSquareResponse(BaseModel):
    dataset_name: str
    group_variable: str
    group_levels: list[str]
    alpha: float
    confirm_independence: bool
    assumptions: list[str]
    variables: list[ChiSquareVariableResult]


class RepeatedMeasuresRequest(BaseModel):
    dataset_id: str
    subject_variable: str
    between_variable: str | None = None
    time_variable: str
    continuous_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)
    confirm_repeated_design: bool = True


class RepeatedMeasuresEffectResult(BaseModel):
    statistic: float | None = None
    df_effect: float | None = None
    df_error: float | None = None
    p_value: float | None = None
    corrected: bool = False


class RepeatedMeasuresTimeSummary(BaseModel):
    time_level: str
    group_level: str | None = None
    n: int
    mean: float | None = None
    sd: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None


class RepeatedMeasuresVariableResult(BaseModel):
    variable: str
    complete_subject_count: int
    excluded_subject_count: int
    duplicate_pair_count: int
    residual_normality_statistic: float | None = None
    residual_normality_p_value: float | None = None
    residual_normality_passed: bool = False
    residual_normality_method: str
    time_sphericity_statistic: float | None = None
    time_sphericity_p_value: float | None = None
    time_sphericity_passed: bool | None = None
    time_gg_epsilon: float | None = None
    time_hf_epsilon: float | None = None
    interaction_sphericity_statistic: float | None = None
    interaction_sphericity_p_value: float | None = None
    interaction_sphericity_passed: bool | None = None
    interaction_gg_epsilon: float | None = None
    interaction_hf_epsilon: float | None = None
    executed_test: str
    note: str
    time_summaries: list[RepeatedMeasuresTimeSummary] = Field(default_factory=list)
    time_effect: RepeatedMeasuresEffectResult
    between_effect: RepeatedMeasuresEffectResult | None = None
    interaction_effect: RepeatedMeasuresEffectResult | None = None


class RepeatedMeasuresResponse(BaseModel):
    dataset_name: str
    subject_variable: str
    between_variable: str | None = None
    between_levels: list[str] = Field(default_factory=list)
    time_variable: str
    time_levels: list[str]
    alpha: float
    confirm_repeated_design: bool
    assumptions: list[str]
    variables: list[RepeatedMeasuresVariableResult]


class LinearRegressionRequest(BaseModel):
    dataset_id: str
    outcome_variable: str
    predictor_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)


class LinearRegressionCoefficient(BaseModel):
    term: str
    estimate: float | None = None
    std_error: float | None = None
    statistic: float | None = None
    p_value: float | None = None
    conf_low: float | None = None
    conf_high: float | None = None


class LinearRegressionResponse(BaseModel):
    dataset_name: str
    outcome_variable: str
    predictor_variables: list[str]
    sample_size: int
    excluded_rows: int
    alpha: float
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    residual_standard_error: float | None = None
    f_statistic: float | None = None
    df_model: float | None = None
    df_residual: float | None = None
    model_p_value: float | None = None
    formula: str
    assumptions: list[str]
    coefficients: list[LinearRegressionCoefficient]
    note: str


class LogisticRegressionRequest(BaseModel):
    dataset_id: str
    outcome_variable: str
    predictor_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)


class LogisticRegressionCoefficient(BaseModel):
    term: str
    odds_ratio: float | None = None
    std_error: float | None = None
    z_value: float | None = None
    p_value: float | None = None
    conf_low: float | None = None
    conf_high: float | None = None


class LogisticRegressionResponse(BaseModel):
    dataset_name: str
    outcome_variable: str
    event_level: str
    reference_level: str
    predictor_variables: list[str]
    sample_size: int
    excluded_rows: int
    alpha: float
    pseudo_r_squared: float | None = None
    aic: float | None = None
    null_deviance: float | None = None
    residual_deviance: float | None = None
    df_model: float | None = None
    df_residual: float | None = None
    model_p_value: float | None = None
    formula: str
    assumptions: list[str]
    coefficients: list[LogisticRegressionCoefficient]
    note: str


class LassoPlotPayload(BaseModel):
    name: str
    filename: str
    media_type: str = "image/png"
    content_base64: str


class LassoFeatureResult(BaseModel):
    term: str
    coefficient_lambda_min: float | None = None
    coefficient_lambda_1se: float | None = None
    selected_at_lambda_min: bool = False
    selected_at_lambda_1se: bool = False


class LassoRegressionRequest(BaseModel):
    dataset_id: str
    outcome_variable: str
    predictor_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)
    nfolds: int = Field(default=10, ge=3, le=20)


class LassoRegressionResponse(BaseModel):
    dataset_name: str
    outcome_variable: str
    predictor_variables: list[str]
    family: Literal["gaussian", "binomial"]
    event_level: str | None = None
    reference_level: str | None = None
    sample_size: int
    excluded_rows: int
    alpha: float
    lambda_min: float
    lambda_1se: float
    nonzero_count_lambda_min: int
    nonzero_count_lambda_1se: int
    assumptions: list[str]
    selected_features: list[LassoFeatureResult]
    plots: list[LassoPlotPayload]
    note: str


class CoxRegressionRequest(BaseModel):
    dataset_id: str
    time_variable: str
    event_variable: str
    predictor_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)


class CoxRegressionCoefficient(BaseModel):
    term: str
    hazard_ratio: float | None = None
    std_error: float | None = None
    z_value: float | None = None
    p_value: float | None = None
    conf_low: float | None = None
    conf_high: float | None = None


class CoxRegressionPhTest(BaseModel):
    term: str
    statistic: float | None = None
    df: float | None = None
    p_value: float | None = None


class CoxRegressionResponse(BaseModel):
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
    concordance: float | None = None
    concordance_std_error: float | None = None
    likelihood_ratio_statistic: float | None = None
    likelihood_ratio_df: float | None = None
    likelihood_ratio_p_value: float | None = None
    wald_statistic: float | None = None
    wald_df: float | None = None
    wald_p_value: float | None = None
    score_statistic: float | None = None
    score_df: float | None = None
    score_p_value: float | None = None
    global_ph_p_value: float | None = None
    formula: str
    assumptions: list[str]
    coefficients: list[CoxRegressionCoefficient]
    proportional_hazards_tests: list[CoxRegressionPhTest]
    note: str


class RegressionInterpretRequest(BaseModel):
    dataset_id: str
    analysis_kind: Literal["linear", "lasso", "logistic"]
    language: Literal["zh", "en"] = "zh"
    payload: dict


class RegressionExportRequest(BaseModel):
    analysis_kind: Literal["linear", "lasso", "logistic"]
    payload: dict


class LassoPlotPdfExportRequest(BaseModel):
    dataset_id: str
    plot: LassoPlotPayload


class RegressionInterpretResponse(BaseModel):
    feature_name: str
    analysis_kind: Literal["linear", "lasso", "logistic"]
    language: Literal["zh", "en"]
    model: str
    content: str
    analysis_id: str | None = None
    saved_at: str | None = None
    llm_tokens_used: int = 0
    charged_tokens: int = 0
    remaining_balance: int = 0


class SavedRegressionInterpretResponse(BaseModel):
    found: bool
    feature_name: str | None = None
    analysis_kind: Literal["linear", "lasso", "logistic"] | None = None
    language: Literal["zh", "en"] | None = None
    model: str | None = None
    content: str | None = None
    analysis_id: str | None = None
    saved_at: str | None = None
    llm_tokens_used: int = 0
    charged_tokens: int = 0
