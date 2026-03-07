"""Endpoints for descriptive statistics and Table 1 generation."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import BadRequest, Forbidden, NotFound
from app.db.database import get_db
from app.db.models.analysis import Analysis, AnalysisResult
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.descriptive import (
    AnovaRequest,
    AnovaResponse,
    AnovaVariableResult,
    ChiSquareLevelRow,
    ChiSquareRequest,
    ChiSquareResponse,
    ChiSquareVariableResult,
    CoxRegressionCoefficient,
    CoxRegressionPhTest,
    CoxRegressionRequest,
    CoxRegressionResponse,
    LassoFeatureResult,
    LassoPlotPayload,
    LassoRegressionRequest,
    LassoRegressionResponse,
    LinearRegressionCoefficient,
    LinearRegressionRequest,
    LinearRegressionResponse,
    LogisticRegressionCoefficient,
    LogisticRegressionRequest,
    LogisticRegressionResponse,
    RepeatedMeasuresEffectResult,
    RepeatedMeasuresRequest,
    RepeatedMeasuresResponse,
    RepeatedMeasuresTimeSummary,
    RepeatedMeasuresVariableResult,
    LassoPlotPdfExportRequest,
    RegressionExportRequest,
    RegressionInterpretRequest,
    RegressionInterpretResponse,
    SavedTableOneInterpretResponse,
    SavedRegressionInterpretResponse,
    TableOneInterpretRequest,
    TableOneInterpretResponse,
    TableOneRequest,
    TableOneResponse,
    TTestGroupSummary,
    TTestNormalityCheck,
    TTestRequest,
    TTestResponse,
    TTestVariableResult,
)
from app.services.storage_service import storage_service
from app.services.anova_service import run_anova
from app.services.chisquare_service import run_chisquare
from app.services.repeated_measures_service import run_repeated_measures_anova
from app.services.regression_interpretation_service import (
    FEATURE_NAME as REGRESSION_FEATURE_NAME,
    build_regression_signature,
    interpret_regression,
)
from app.services.regression_export_service import export_regression_excel
from app.services.regression_pdf_service import export_lasso_plot_pdf
from app.services.regression_service import (
    run_cox_regression,
    run_lasso_regression,
    run_linear_regression,
    run_logistic_regression,
)
from app.services.tableone_interpretation_service import FEATURE_NAME, build_tableone_signature, interpret_tableone
from app.services.tableone_service import generate_tableone
from app.services.ttest_service import run_ttest
from app.services.user_service import calculate_ai_interpretation_charge, consume_user_tokens
from app.services.dataset_parser import load_tabular_dataframe
from app.services.dataset_kind_service import get_dataset_kind_overrides


router = APIRouter(prefix="/descriptive", tags=["描述统计"])
PAID_SUBSCRIPTIONS = {"basic", "pro", "enterprise"}


async def _get_dataset_for_user(dataset_id: uuid.UUID, current_user: User, db: AsyncSession) -> Dataset:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise NotFound("数据集不存在")

    project_result = await db.execute(select(Project).where(Project.id == dataset.project_id))
    project = project_result.scalar_one_or_none()
    if not project or project.owner_id != current_user.id:
        raise Forbidden("无权查看该数据集")
    return dataset


async def _get_saved_interpretation(
    db: AsyncSession,
    dataset: Dataset,
    current_user: User,
    payload: TableOneInterpretRequest,
) -> AnalysisResult | None:
    signature = build_tableone_signature(payload.table, payload.language)
    result = await db.execute(
        select(Analysis, AnalysisResult)
        .join(AnalysisResult, AnalysisResult.analysis_id == Analysis.id)
        .where(
            Analysis.project_id == dataset.project_id,
            Analysis.dataset_id == dataset.id,
            Analysis.created_by == current_user.id,
            Analysis.analysis_type == "table1_interpretation",
            Analysis.status == "completed",
        )
        .order_by(Analysis.executed_at.desc(), Analysis.created_at.desc())
    )

    for analysis, analysis_result in result.all():
        configuration = analysis.configuration or {}
        if configuration.get("table_signature") == signature:
            return analysis_result
    return None


async def _get_saved_regression_interpretation(
    db: AsyncSession,
    dataset: Dataset,
    current_user: User,
    payload: RegressionInterpretRequest,
) -> AnalysisResult | None:
    signature = build_regression_signature(payload.analysis_kind, payload.payload, payload.language)
    expected_analysis_type = f"{payload.analysis_kind}_regression_interpretation"
    result = await db.execute(
        select(Analysis, AnalysisResult)
        .join(AnalysisResult, AnalysisResult.analysis_id == Analysis.id)
        .where(
            Analysis.project_id == dataset.project_id,
            Analysis.dataset_id == dataset.id,
            Analysis.created_by == current_user.id,
            Analysis.analysis_type == expected_analysis_type,
            Analysis.status == "completed",
        )
        .order_by(Analysis.executed_at.desc(), Analysis.created_at.desc())
    )

    for analysis, analysis_result in result.all():
        configuration = analysis.configuration or {}
        if configuration.get("regression_signature") == signature:
            return analysis_result
    return None


def _ensure_paid_ai_interpretation_access(current_user: User) -> None:
    if current_user.subscription not in PAID_SUBSCRIPTIONS:
        raise Forbidden("AI结果解读为付费功能，请升级后使用")
    if current_user.token_balance < 500:
        raise BadRequest("Token 余额不足，AI结果解读至少需要 500 Token")


async def _save_ai_interpretation_analysis(
    *,
    db: AsyncSession,
    dataset: Dataset,
    current_user: User,
    analysis_name: str,
    analysis_type: str,
    configuration: dict,
    result_data: dict,
    tables: dict | None,
    charged_tokens: int,
    executed_at: datetime,
) -> AnalysisResult:
    analysis = Analysis(
        project_id=dataset.project_id,
        dataset_id=dataset.id,
        name=analysis_name,
        analysis_type=analysis_type,
        configuration=configuration,
        status="completed",
        tokens_consumed=charged_tokens,
        created_by=current_user.id,
        executed_at=executed_at,
    )
    db.add(analysis)
    await db.flush()

    analysis_result = AnalysisResult(
        analysis_id=analysis.id,
        result_data=result_data,
        tables=tables,
    )
    db.add(analysis_result)
    await db.flush()
    return analysis_result


@router.post("/table1", response_model=TableOneResponse)
async def preview_tableone(
    payload: TableOneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate Table 1 preview."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = generate_tableone(
        content=content,
        ext=ext,
        dataset_name=dataset.name,
        group_variable=payload.group_variable,
        variables=payload.variables,
        decimals=payload.decimals,
        type_overrides=kind_overrides,
    )

    return TableOneResponse(
        title=result.title,
        dataset_name=result.dataset_name,
        group_variable=result.group_variable,
        group_levels=result.group_levels,
        headers=result.headers,
        rows=result.rows,
        continuous_variables=result.continuous_variables,
        categorical_variables=result.categorical_variables,
        nonnormal_variables=result.nonnormal_variables,
        normality_method=result.normality_method,
    )


@router.post("/ttest", response_model=TTestResponse)
async def run_independent_ttest(
    payload: TTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run independent-samples t-test workflow with R."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)

    result = run_ttest(
        df=df,
        dataset_name=dataset.name,
        group_variable=payload.group_variable,
        continuous_variables=payload.continuous_variables,
        alpha=payload.alpha,
        confirm_independence=payload.confirm_independence,
    )

    return TTestResponse(
        dataset_name=result.dataset_name,
        group_variable=result.group_variable,
        group_levels=result.group_levels,
        alpha=result.alpha,
        confirm_independence=result.confirm_independence,
        assumptions=result.assumptions,
        variables=[
            TTestVariableResult(
                variable=item.variable,
                group_summaries=[
                    TTestGroupSummary(
                        group=group_summary.group,
                        n=group_summary.n,
                        mean=group_summary.mean,
                        sd=group_summary.sd,
                        median=group_summary.median,
                        q1=group_summary.q1,
                        q3=group_summary.q3,
                    )
                    for group_summary in item.group_summaries
                ],
                normality_checks=[
                    TTestNormalityCheck(
                        group=normality.group,
                        n=normality.n,
                        p_value=normality.p_value,
                        passed=normality.passed,
                        method=normality.method,
                    )
                    for normality in item.normality_checks
                ],
                variance_test_name=item.variance_test_name,
                variance_p_value=item.variance_p_value,
                equal_variance=item.equal_variance,
                satisfies_t_test=item.satisfies_t_test,
                recommended_test=item.recommended_test,
                executed_test=item.executed_test,
                statistic=item.statistic,
                df=item.df,
                p_value=item.p_value,
                estimate=item.estimate,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
                note=item.note,
            )
            for item in result.variables
        ],
    )


@router.post("/anova", response_model=AnovaResponse)
async def run_one_way_anova(
    payload: AnovaRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run one-way ANOVA workflow with automatic Kruskal-Wallis fallback via R."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)

    result = run_anova(
        df=df,
        dataset_name=dataset.name,
        group_variable=payload.group_variable,
        continuous_variables=payload.continuous_variables,
        alpha=payload.alpha,
        confirm_independence=payload.confirm_independence,
    )

    return AnovaResponse(
        dataset_name=result.dataset_name,
        group_variable=result.group_variable,
        group_levels=result.group_levels,
        alpha=result.alpha,
        confirm_independence=result.confirm_independence,
        assumptions=result.assumptions,
        variables=[
            AnovaVariableResult(
                variable=item.variable,
                group_summaries=[
                    TTestGroupSummary(
                        group=group_summary.group,
                        n=group_summary.n,
                        mean=group_summary.mean,
                        sd=group_summary.sd,
                        median=group_summary.median,
                        q1=group_summary.q1,
                        q3=group_summary.q3,
                    )
                    for group_summary in item.group_summaries
                ],
                normality_checks=[
                    TTestNormalityCheck(
                        group=normality.group,
                        n=normality.n,
                        p_value=normality.p_value,
                        passed=normality.passed,
                        method=normality.method,
                    )
                    for normality in item.normality_checks
                ],
                variance_test_name=item.variance_test_name,
                variance_p_value=item.variance_p_value,
                equal_variance=item.equal_variance,
                satisfies_anova=item.satisfies_anova,
                recommended_test=item.recommended_test,
                executed_test=item.executed_test,
                statistic=item.statistic,
                df_between=item.df_between,
                df_within=item.df_within,
                p_value=item.p_value,
                note=item.note,
            )
            for item in result.variables
        ],
    )


@router.post("/chisquare", response_model=ChiSquareResponse)
async def run_chi_square_test(
    payload: ChiSquareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run chi-squared workflow with Fisher fallback via R."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)

    result = run_chisquare(
        df=df,
        dataset_name=dataset.name,
        group_variable=payload.group_variable,
        categorical_variables=payload.categorical_variables,
        alpha=payload.alpha,
        confirm_independence=payload.confirm_independence,
    )

    return ChiSquareResponse(
        dataset_name=result.dataset_name,
        group_variable=result.group_variable,
        group_levels=result.group_levels,
        alpha=result.alpha,
        confirm_independence=result.confirm_independence,
        assumptions=result.assumptions,
        variables=[
            ChiSquareVariableResult(
                variable=item.variable,
                level_rows=[
                    ChiSquareLevelRow(level=level_row.level, group_values=level_row.group_values)
                    for level_row in item.level_rows
                ],
                minimum_expected_count=item.minimum_expected_count,
                expected_count_warning=item.expected_count_warning,
                recommended_test=item.recommended_test,
                executed_test=item.executed_test,
                statistic=item.statistic,
                df=item.df,
                p_value=item.p_value,
                note=item.note,
            )
            for item in result.variables
        ],
    )


@router.post("/repeated-measures-anova", response_model=RepeatedMeasuresResponse)
async def run_repeated_measures_anova_endpoint(
    payload: RepeatedMeasuresRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run repeated-measures ANOVA workflow with assumption-aware fallback via R."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)

    result = run_repeated_measures_anova(
        df=df,
        dataset_name=dataset.name,
        subject_variable=payload.subject_variable,
        between_variable=payload.between_variable,
        time_variable=payload.time_variable,
        continuous_variables=payload.continuous_variables,
        alpha=payload.alpha,
        confirm_repeated_design=payload.confirm_repeated_design,
    )

    return RepeatedMeasuresResponse(
        dataset_name=result.dataset_name,
        subject_variable=result.subject_variable,
        between_variable=result.between_variable,
        between_levels=result.between_levels,
        time_variable=result.time_variable,
        time_levels=result.time_levels,
        alpha=result.alpha,
        confirm_repeated_design=result.confirm_repeated_design,
        assumptions=result.assumptions,
        variables=[
            RepeatedMeasuresVariableResult(
                variable=item.variable,
                complete_subject_count=item.complete_subject_count,
                excluded_subject_count=item.excluded_subject_count,
                duplicate_pair_count=item.duplicate_pair_count,
                residual_normality_statistic=item.residual_normality_statistic,
                residual_normality_p_value=item.residual_normality_p_value,
                residual_normality_passed=item.residual_normality_passed,
                residual_normality_method=item.residual_normality_method,
                time_sphericity_statistic=item.time_sphericity_statistic,
                time_sphericity_p_value=item.time_sphericity_p_value,
                time_sphericity_passed=item.time_sphericity_passed,
                time_gg_epsilon=item.time_gg_epsilon,
                time_hf_epsilon=item.time_hf_epsilon,
                interaction_sphericity_statistic=item.interaction_sphericity_statistic,
                interaction_sphericity_p_value=item.interaction_sphericity_p_value,
                interaction_sphericity_passed=item.interaction_sphericity_passed,
                interaction_gg_epsilon=item.interaction_gg_epsilon,
                interaction_hf_epsilon=item.interaction_hf_epsilon,
                executed_test=item.executed_test,
                note=item.note,
                time_summaries=[
                    RepeatedMeasuresTimeSummary(
                        time_level=summary.time_level,
                        group_level=summary.group_level,
                        n=summary.n,
                        mean=summary.mean,
                        sd=summary.sd,
                        median=summary.median,
                        q1=summary.q1,
                        q3=summary.q3,
                    )
                    for summary in item.time_summaries
                ],
                time_effect=RepeatedMeasuresEffectResult(
                    statistic=item.time_effect.statistic,
                    df_effect=item.time_effect.df_effect,
                    df_error=item.time_effect.df_error,
                    p_value=item.time_effect.p_value,
                    corrected=item.time_effect.corrected,
                ),
                between_effect=(
                    None
                    if item.between_effect is None
                    else RepeatedMeasuresEffectResult(
                        statistic=item.between_effect.statistic,
                        df_effect=item.between_effect.df_effect,
                        df_error=item.between_effect.df_error,
                        p_value=item.between_effect.p_value,
                        corrected=item.between_effect.corrected,
                    )
                ),
                interaction_effect=(
                    None
                    if item.interaction_effect is None
                    else RepeatedMeasuresEffectResult(
                        statistic=item.interaction_effect.statistic,
                        df_effect=item.interaction_effect.df_effect,
                        df_error=item.interaction_effect.df_error,
                        p_value=item.interaction_effect.p_value,
                        corrected=item.interaction_effect.corrected,
                    )
                ),
            )
            for item in result.variables
        ],
    )


@router.post("/linear-regression", response_model=LinearRegressionResponse)
async def run_linear_regression_endpoint(
    payload: LinearRegressionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = run_linear_regression(
        df=df,
        dataset_name=dataset.name,
        outcome_variable=payload.outcome_variable,
        predictor_variables=payload.predictor_variables,
        alpha=payload.alpha,
        predictor_kind_overrides=kind_overrides,
    )

    return LinearRegressionResponse(
        dataset_name=result.dataset_name,
        outcome_variable=result.outcome_variable,
        predictor_variables=result.predictor_variables,
        sample_size=result.sample_size,
        excluded_rows=result.excluded_rows,
        alpha=result.alpha,
        r_squared=result.r_squared,
        adjusted_r_squared=result.adjusted_r_squared,
        residual_standard_error=result.residual_standard_error,
        f_statistic=result.f_statistic,
        df_model=result.df_model,
        df_residual=result.df_residual,
        model_p_value=result.model_p_value,
        formula=result.formula,
        assumptions=result.assumptions,
        coefficients=[
            LinearRegressionCoefficient(
                term=item.term,
                estimate=item.estimate,
                std_error=item.std_error,
                statistic=item.statistic,
                p_value=item.p_value,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
            )
            for item in result.coefficients
        ],
        note=result.note,
    )


@router.post("/logistic-regression", response_model=LogisticRegressionResponse)
async def run_logistic_regression_endpoint(
    payload: LogisticRegressionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = run_logistic_regression(
        df=df,
        dataset_name=dataset.name,
        outcome_variable=payload.outcome_variable,
        predictor_variables=payload.predictor_variables,
        alpha=payload.alpha,
        predictor_kind_overrides=kind_overrides,
    )

    return LogisticRegressionResponse(
        dataset_name=result.dataset_name,
        outcome_variable=result.outcome_variable,
        event_level=result.event_level,
        reference_level=result.reference_level,
        predictor_variables=result.predictor_variables,
        sample_size=result.sample_size,
        excluded_rows=result.excluded_rows,
        alpha=result.alpha,
        pseudo_r_squared=result.pseudo_r_squared,
        aic=result.aic,
        null_deviance=result.null_deviance,
        residual_deviance=result.residual_deviance,
        df_model=result.df_model,
        df_residual=result.df_residual,
        model_p_value=result.model_p_value,
        formula=result.formula,
        assumptions=result.assumptions,
        coefficients=[
            LogisticRegressionCoefficient(
                term=item.term,
                odds_ratio=item.odds_ratio,
                std_error=item.std_error,
                z_value=item.z_value,
                p_value=item.p_value,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
            )
            for item in result.coefficients
        ],
        note=result.note,
    )


@router.post("/lasso-regression", response_model=LassoRegressionResponse)
async def run_lasso_regression_endpoint(
    payload: LassoRegressionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = run_lasso_regression(
        df=df,
        dataset_name=dataset.name,
        outcome_variable=payload.outcome_variable,
        predictor_variables=payload.predictor_variables,
        alpha=payload.alpha,
        nfolds=payload.nfolds,
        predictor_kind_overrides=kind_overrides,
    )

    return LassoRegressionResponse(
        dataset_name=result.dataset_name,
        outcome_variable=result.outcome_variable,
        predictor_variables=result.predictor_variables,
        family=result.family,
        event_level=result.event_level,
        reference_level=result.reference_level,
        sample_size=result.sample_size,
        excluded_rows=result.excluded_rows,
        alpha=result.alpha,
        lambda_min=result.lambda_min,
        lambda_1se=result.lambda_1se,
        nonzero_count_lambda_min=result.nonzero_count_lambda_min,
        nonzero_count_lambda_1se=result.nonzero_count_lambda_1se,
        assumptions=result.assumptions,
        selected_features=[
            LassoFeatureResult(
                term=item.term,
                coefficient_lambda_min=item.coefficient_lambda_min,
                coefficient_lambda_1se=item.coefficient_lambda_1se,
                selected_at_lambda_min=item.selected_at_lambda_min,
                selected_at_lambda_1se=item.selected_at_lambda_1se,
            )
            for item in result.selected_features
        ],
        plots=[
            LassoPlotPayload(
                name=plot.name,
                filename=plot.filename,
                media_type=plot.media_type,
                content_base64=plot.content_base64,
            )
            for plot in result.plots
        ],
        note=result.note,
    )


@router.post("/cox-regression", response_model=CoxRegressionResponse)
async def run_cox_regression_endpoint(
    payload: CoxRegressionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("Invalid dataset id") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    df = load_tabular_dataframe(content, ext)
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = run_cox_regression(
        df=df,
        dataset_name=dataset.name,
        time_variable=payload.time_variable,
        event_variable=payload.event_variable,
        predictor_variables=payload.predictor_variables,
        alpha=payload.alpha,
        predictor_kind_overrides=kind_overrides,
    )

    return CoxRegressionResponse(
        dataset_name=result.dataset_name,
        time_variable=result.time_variable,
        event_variable=result.event_variable,
        event_level=result.event_level,
        reference_level=result.reference_level,
        predictor_variables=result.predictor_variables,
        sample_size=result.sample_size,
        event_count=result.event_count,
        excluded_rows=result.excluded_rows,
        alpha=result.alpha,
        concordance=result.concordance,
        concordance_std_error=result.concordance_std_error,
        likelihood_ratio_statistic=result.likelihood_ratio_statistic,
        likelihood_ratio_df=result.likelihood_ratio_df,
        likelihood_ratio_p_value=result.likelihood_ratio_p_value,
        wald_statistic=result.wald_statistic,
        wald_df=result.wald_df,
        wald_p_value=result.wald_p_value,
        score_statistic=result.score_statistic,
        score_df=result.score_df,
        score_p_value=result.score_p_value,
        global_ph_p_value=result.global_ph_p_value,
        formula=result.formula,
        assumptions=result.assumptions,
        coefficients=[
            CoxRegressionCoefficient(
                term=item.term,
                hazard_ratio=item.hazard_ratio,
                std_error=item.std_error,
                z_value=item.z_value,
                p_value=item.p_value,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
            )
            for item in result.coefficients
        ],
        proportional_hazards_tests=[
            CoxRegressionPhTest(
                term=item.term,
                statistic=item.statistic,
                df=item.df,
                p_value=item.p_value,
            )
            for item in result.proportional_hazards_tests
        ],
        note=result.note,
    )


@router.post("/table1/export")
async def export_tableone(
    payload: TableOneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export Table 1 as an Excel workbook."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = generate_tableone(
        content=content,
        ext=ext,
        dataset_name=dataset.name,
        group_variable=payload.group_variable,
        variables=payload.variables,
        decimals=payload.decimals,
        type_overrides=kind_overrides,
    )

    file_name = f"{Path(result.dataset_name).stem}_table1.xlsx"
    encoded_file_name = quote(file_name)
    return Response(
        content=result.excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"},
    )


@router.post("/regression/export")
async def export_regression_result(
    payload: RegressionExportRequest,
    current_user: User = Depends(get_current_user),
):
    del current_user
    excel_content = export_regression_excel(payload.analysis_kind, payload.payload)
    dataset_name = str(payload.payload.get("dataset_name") or "regression")
    file_name = f"{Path(dataset_name).stem}_{payload.analysis_kind}_regression.xlsx"
    encoded_file_name = quote(file_name)
    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"},
    )


@router.post("/lasso-regression/plot/pdf")
async def export_lasso_plot_pdf_result(
    payload: LassoPlotPdfExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.subscription not in PAID_SUBSCRIPTIONS:
        raise Forbidden("PDF 下载为付费会员功能，请升级后使用")

    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    await _get_dataset_for_user(dataset_uuid, current_user, db)
    pdf_content, file_name = export_lasso_plot_pdf(payload.plot)
    encoded_file_name = quote(file_name)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"},
    )


@router.post("/table1/interpret", response_model=TableOneInterpretResponse)
async def interpret_tableone_result(
    payload: TableOneInterpretRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Interpret Table 1 using an LLM for paid users."""
    _ensure_paid_ai_interpretation_access(current_user)

    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    interpretation = await interpret_tableone(payload.table, payload.language)
    charged_tokens = calculate_ai_interpretation_charge(interpretation.llm_tokens_used)
    remaining_balance = await consume_user_tokens(
        db=db,
        user=current_user,
        operation="table1_interpretation",
        billed_tokens=charged_tokens,
        actual_tokens=interpretation.llm_tokens_used,
    )
    now = datetime.now(timezone.utc)
    signature = build_tableone_signature(payload.table, payload.language)
    analysis_result = await _save_ai_interpretation_analysis(
        db=db,
        dataset=dataset,
        current_user=current_user,
        analysis_name=f"Table 1 AI???? ? {payload.table.group_variable}",
        analysis_type="table1_interpretation",
        configuration={
            "group_variable": payload.table.group_variable,
            "group_levels": payload.table.group_levels,
            "continuous_variables": payload.table.continuous_variables,
            "categorical_variables": payload.table.categorical_variables,
            "nonnormal_variables": payload.table.nonnormal_variables,
            "language": payload.language,
            "table_signature": signature,
        },
        result_data={
            "feature_name": FEATURE_NAME,
            "language": payload.language,
            "model": interpretation.model,
            "content": interpretation.content,
            "llm_tokens_used": interpretation.llm_tokens_used,
            "charged_tokens": charged_tokens,
        },
        tables={"table1": payload.table.model_dump()},
        charged_tokens=charged_tokens,
        executed_at=now,
    )

    return TableOneInterpretResponse(
        feature_name=FEATURE_NAME,
        language=payload.language,
        model=interpretation.model,
        content=interpretation.content,
        analysis_id=str(analysis_result.analysis_id),
        saved_at=analysis_result.created_at.isoformat() if analysis_result.created_at else now.isoformat(),
        llm_tokens_used=interpretation.llm_tokens_used,
        charged_tokens=charged_tokens,
        remaining_balance=remaining_balance,
    )


@router.post("/table1/interpret/saved", response_model=SavedTableOneInterpretResponse)
async def get_saved_tableone_interpretation(
    payload: TableOneInterpretRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch the latest saved AI interpretation for the current Table 1 signature."""
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    saved = await _get_saved_interpretation(db, dataset, current_user, payload)
    if not saved:
        return SavedTableOneInterpretResponse(found=False)

    result_data = saved.result_data or {}
    return SavedTableOneInterpretResponse(
        found=True,
        feature_name=str(result_data.get("feature_name") or FEATURE_NAME),
        language=result_data.get("language") or payload.language,
        model=result_data.get("model"),
        content=result_data.get("content"),
        analysis_id=str(saved.analysis_id),
        saved_at=saved.created_at.isoformat() if saved.created_at else None,
        llm_tokens_used=int(result_data.get("llm_tokens_used") or result_data.get("actual_tokens") or 0),
        charged_tokens=int(result_data.get("charged_tokens") or result_data.get("billed_tokens") or 0),
    )


@router.post("/regression/interpret", response_model=RegressionInterpretResponse)
async def interpret_regression_result(
    payload: RegressionInterpretRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_paid_ai_interpretation_access(current_user)

    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    interpretation = await interpret_regression(payload.analysis_kind, payload.payload, payload.language)
    charged_tokens = calculate_ai_interpretation_charge(interpretation.llm_tokens_used)
    remaining_balance = await consume_user_tokens(
        db=db,
        user=current_user,
        operation=f"{payload.analysis_kind}_regression_interpretation",
        billed_tokens=charged_tokens,
        actual_tokens=interpretation.llm_tokens_used,
    )
    now = datetime.now(timezone.utc)
    signature = build_regression_signature(payload.analysis_kind, payload.payload, payload.language)
    analysis_type = f"{payload.analysis_kind}_regression_interpretation"
    analysis_result = await _save_ai_interpretation_analysis(
        db=db,
        dataset=dataset,
        current_user=current_user,
        analysis_name=f"{payload.analysis_kind} regression interpretation",
        analysis_type=analysis_type,
        configuration={
            "analysis_kind": payload.analysis_kind,
            "language": payload.language,
            "regression_signature": signature,
        },
        result_data={
            "feature_name": REGRESSION_FEATURE_NAME,
            "analysis_kind": payload.analysis_kind,
            "language": payload.language,
            "model": interpretation.model,
            "content": interpretation.content,
            "llm_tokens_used": interpretation.llm_tokens_used,
            "charged_tokens": charged_tokens,
        },
        tables={"regression": payload.payload},
        charged_tokens=charged_tokens,
        executed_at=now,
    )

    return RegressionInterpretResponse(
        feature_name=REGRESSION_FEATURE_NAME,
        analysis_kind=payload.analysis_kind,
        language=payload.language,
        model=interpretation.model,
        content=interpretation.content,
        analysis_id=str(analysis_result.analysis_id),
        saved_at=analysis_result.created_at.isoformat() if analysis_result.created_at else now.isoformat(),
        llm_tokens_used=interpretation.llm_tokens_used,
        charged_tokens=charged_tokens,
        remaining_balance=remaining_balance,
    )


@router.post("/regression/interpret/saved", response_model=SavedRegressionInterpretResponse)
async def get_saved_regression_interpretation(
    payload: RegressionInterpretRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
    except ValueError as exc:
        raise BadRequest("数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    saved = await _get_saved_regression_interpretation(db, dataset, current_user, payload)
    if not saved:
        return SavedRegressionInterpretResponse(found=False)

    result_data = saved.result_data or {}
    return SavedRegressionInterpretResponse(
        found=True,
        feature_name=str(result_data.get("feature_name") or REGRESSION_FEATURE_NAME),
        analysis_kind=result_data.get("analysis_kind") or payload.analysis_kind,
        language=result_data.get("language") or payload.language,
        model=result_data.get("model"),
        content=result_data.get("content"),
        analysis_id=str(saved.analysis_id),
        saved_at=saved.created_at.isoformat() if saved.created_at else None,
        llm_tokens_used=int(result_data.get("llm_tokens_used") or result_data.get("actual_tokens") or 0),
        charged_tokens=int(result_data.get("charged_tokens") or result_data.get("billed_tokens") or 0),
    )
