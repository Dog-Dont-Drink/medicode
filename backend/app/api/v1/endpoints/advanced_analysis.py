"""Endpoints for advanced clinical modeling pipelines."""

from __future__ import annotations

import uuid
import base64
from urllib.parse import quote
from datetime import timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import BadRequest, Forbidden, NotFound
from app.db.database import get_db
from app.db.models.dataset import Dataset
from app.db.models.project import Project
from app.db.models.project_workflow import ProjectWorkflow
from app.db.models.user import User
from app.db.models.workflow_run import WorkflowArtifact, WorkflowRun, WorkflowRunNode
from app.schemas.advanced_analysis import (
    ClinicalPipelineDatasetState,
    ClinicalPipelineNodeDetailResponse,
    ClinicalPipelineNodeResult,
    ClinicalPipelineRunDetailResponse,
    ClinicalPipelineRunRequest,
    ClinicalPipelineRunResponse,
    ClinicalPipelineRunSummaryResponse,
    ClinicalPipelineArtifactResult,
    ClinicalWorkflowDetailResponse,
    ClinicalWorkflowSaveRequest,
    ClinicalWorkflowSummaryResponse,
    ClinicalWorkflowUpdateRequest,
    ClinicalWorkflowValidationIssue,
    ClinicalWorkflowValidationRequest,
    ClinicalWorkflowValidationResponse,
    SavedClinicalWorkflowConnection,
    SavedClinicalWorkflowNode,
)
from app.schemas.dataset import ColumnSummaryResponse, DatasetSummaryResponse, ValueFrequencyResponse
from app.schemas.descriptive import (
    CoxRegressionCoefficient,
    CoxRegressionPhTest,
    CoxRegressionResponse,
    LassoFeatureResult,
    LassoPlotPayload,
    LassoRegressionResponse,
    LogisticRegressionCoefficient,
    LogisticRegressionResponse,
)
from app.services.advanced_modeling_service import ClinicalPipelineExecutionResult, run_clinical_prediction_pipeline
from app.services.clinical_workflow_validation_service import validate_clinical_workflow
from app.services.dataset_kind_service import get_dataset_kind_overrides
from app.services.storage_service import storage_service
from app.services.workflow_run_service import persist_clinical_pipeline_run


router = APIRouter(prefix="/advanced-analysis", tags=["高级分析"])


def _utc_isoformat(value) -> str | None:
    if value is None:
        return None
    dt = value
    tzinfo = getattr(dt, "tzinfo", None)
    if tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _build_content_disposition(filename: str) -> str:
    safe_ascii = "".join(char if ord(char) < 128 else "_" for char in filename).strip() or "artifact.bin"
    encoded = quote(filename, safe="")
    return f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'


async def _get_project_for_user(project_id: uuid.UUID, current_user: User, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("项目不存在")
    if project.owner_id != current_user.id:
        raise Forbidden("无权访问该项目")
    return project


async def _get_run_for_user(run_id: uuid.UUID, current_user: User, db: AsyncSession) -> WorkflowRun:
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise NotFound("运行记录不存在")
    if run.owner_id != current_user.id:
        raise Forbidden("无权访问该运行记录")
    return run


async def _get_artifact_for_user(artifact_id: uuid.UUID, current_user: User, db: AsyncSession) -> WorkflowArtifact:
    result = await db.execute(select(WorkflowArtifact).where(WorkflowArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise NotFound("产物不存在")
    if artifact.owner_id != current_user.id:
        raise Forbidden("无权访问该产物")
    return artifact


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


def _validate_or_raise(nodes, connections) -> None:
    validation = validate_clinical_workflow(nodes, connections)
    if validation.is_valid:
        return
    errors = [item.message for item in validation.issues if item.severity == "error"]
    raise BadRequest("；".join(errors[:6]))


def _workflow_payload(nodes: list[SavedClinicalWorkflowNode], connections: list[SavedClinicalWorkflowConnection]) -> dict:
    return {
        "nodes": [node.model_dump() for node in nodes],
        "connections": [connection.model_dump() for connection in connections],
    }


def _map_workflow_summary(workflow: ProjectWorkflow) -> ClinicalWorkflowSummaryResponse:
    payload = workflow.payload or {}
    nodes = payload.get("nodes") or []
    conns = payload.get("connections") or []
    return ClinicalWorkflowSummaryResponse(
        id=str(workflow.id),
        project_id=str(workflow.project_id),
        name=workflow.name,
        description=workflow.description,
        workflow_kind=workflow.workflow_kind,
        node_count=len(nodes),
        connection_count=len(conns),
        created_at=_utc_isoformat(workflow.created_at) or "",
        updated_at=_utc_isoformat(workflow.updated_at) or _utc_isoformat(workflow.created_at) or "",
    )


def _map_workflow_detail(workflow: ProjectWorkflow) -> ClinicalWorkflowDetailResponse:
    summary = _map_workflow_summary(workflow)
    payload = workflow.payload or {}
    nodes = payload.get("nodes") or []
    conns = payload.get("connections") or []
    return ClinicalWorkflowDetailResponse(
        **summary.model_dump(),
        nodes=[SavedClinicalWorkflowNode.model_validate(item) for item in nodes],
        connections=[SavedClinicalWorkflowConnection.model_validate(item) for item in conns],
    )


async def _get_workflow_for_user(workflow_id: uuid.UUID, current_user: User, db: AsyncSession) -> ProjectWorkflow:
    result = await db.execute(select(ProjectWorkflow).where(ProjectWorkflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise NotFound("流程不存在")
    if workflow.owner_id != current_user.id:
        raise Forbidden("无权访问该流程")
    return workflow


@router.get("/workflows", response_model=list[ClinicalWorkflowSummaryResponse])
async def list_clinical_workflows(
    project_id: str,
    workflow_kind: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError as exc:
        raise BadRequest("project_id 无效") from exc

    await _get_project_for_user(project_uuid, current_user, db)
    query = select(ProjectWorkflow).where(ProjectWorkflow.project_id == project_uuid, ProjectWorkflow.owner_id == current_user.id)
    if workflow_kind:
        query = query.where(ProjectWorkflow.workflow_kind == workflow_kind)
    query = query.order_by(ProjectWorkflow.updated_at.desc())
    result = await db.execute(query)
    workflows = result.scalars().all()
    return [_map_workflow_summary(item) for item in workflows]


@router.get("/workflows/{workflow_id}", response_model=ClinicalWorkflowDetailResponse)
async def get_clinical_workflow_detail(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        workflow_uuid = uuid.UUID(workflow_id)
    except ValueError as exc:
        raise BadRequest("workflow_id 无效") from exc
    workflow = await _get_workflow_for_user(workflow_uuid, current_user, db)
    return _map_workflow_detail(workflow)


@router.post("/workflows", response_model=ClinicalWorkflowDetailResponse)
async def save_clinical_workflow(
    payload: ClinicalWorkflowSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        project_uuid = uuid.UUID(payload.project_id)
    except ValueError as exc:
        raise BadRequest("project_id 无效") from exc
    await _get_project_for_user(project_uuid, current_user, db)

    workflow_kind = payload.workflow_kind or "clinical_prediction"
    workflow = ProjectWorkflow(
        project_id=project_uuid,
        owner_id=current_user.id,
        name=payload.name.strip() or "Untitled",
        description=payload.description,
        workflow_kind=workflow_kind,
        payload=_workflow_payload(payload.nodes, payload.connections),
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return _map_workflow_detail(workflow)


@router.put("/workflows/{workflow_id}", response_model=ClinicalWorkflowDetailResponse)
async def update_clinical_workflow(
    workflow_id: str,
    payload: ClinicalWorkflowUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        workflow_uuid = uuid.UUID(workflow_id)
    except ValueError as exc:
        raise BadRequest("workflow_id 无效") from exc
    workflow = await _get_workflow_for_user(workflow_uuid, current_user, db)

    workflow.name = payload.name.strip() or workflow.name
    workflow.description = payload.description
    workflow.payload = _workflow_payload(payload.nodes, payload.connections)
    await db.commit()
    await db.refresh(workflow)
    return _map_workflow_detail(workflow)


@router.delete("/workflows/{workflow_id}")
async def delete_clinical_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        workflow_uuid = uuid.UUID(workflow_id)
    except ValueError as exc:
        raise BadRequest("workflow_id 无效") from exc
    workflow = await _get_workflow_for_user(workflow_uuid, current_user, db)
    await db.delete(workflow)
    await db.commit()
    return {"success": True}


@router.post("/workflows/validate", response_model=ClinicalWorkflowValidationResponse)
async def validate_saved_workflow(
    payload: ClinicalWorkflowValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        project_uuid = uuid.UUID(payload.project_id)
    except ValueError as exc:
        raise BadRequest("project_id 无效") from exc
    await _get_project_for_user(project_uuid, current_user, db)

    validation = validate_clinical_workflow(payload.nodes, payload.connections)
    issues = [
        ClinicalWorkflowValidationIssue(
            severity=item.severity,
            code=item.code,
            message=item.message,
            node_id=item.node_id,
            connection_id=item.connection_id,
        )
        for item in (validation.issues or [])
    ]
    return ClinicalWorkflowValidationResponse(
        is_valid=validation.is_valid,
        issues=issues,
        root_node_ids=validation.root_node_ids,
        leaf_node_ids=validation.leaf_node_ids,
    )


def _map_summary(summary) -> DatasetSummaryResponse:
    return DatasetSummaryResponse(
        total_rows=summary.total_rows,
        total_columns=summary.total_columns,
        numeric_columns=summary.numeric_columns,
        categorical_columns=summary.categorical_columns,
        datetime_columns=summary.datetime_columns,
        boolean_columns=summary.boolean_columns,
        complete_rows=summary.complete_rows,
        duplicate_rows=summary.duplicate_rows,
        missing_cells=summary.missing_cells,
        missing_rate=summary.missing_rate,
        columns=[
            ColumnSummaryResponse(
                name=column.name,
                kind=column.kind,
                kind_source=column.kind_source,
                non_null_count=column.non_null_count,
                missing_count=column.missing_count,
                missing_rate=column.missing_rate,
                unique_count=column.unique_count,
                sample_values=column.sample_values,
                numeric_min=column.numeric_min,
                numeric_max=column.numeric_max,
                numeric_mean=column.numeric_mean,
                numeric_std=column.numeric_std,
                numeric_median=column.numeric_median,
                numeric_q1=column.numeric_q1,
                numeric_q3=column.numeric_q3,
                datetime_min=column.datetime_min,
                datetime_max=column.datetime_max,
                top_values=[
                    ValueFrequencyResponse(value=item.value, count=item.count, ratio=item.ratio)
                    for item in (column.top_values or [])
                ] or None,
            )
            for column in summary.columns
        ],
    )


def _map_lasso(result) -> LassoRegressionResponse:
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
                vector_pdf_filename=plot.vector_pdf_filename,
                vector_pdf_base64=plot.vector_pdf_base64,
            )
            for plot in result.plots
        ],
        note=result.note,
    )


def _map_logistic(result) -> LogisticRegressionResponse:
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
        univariate_coefficients=[
            LogisticRegressionCoefficient(
                term=item.term,
                coefficient=item.coefficient,
                odds_ratio=item.odds_ratio,
                std_error=item.std_error,
                z_value=item.z_value,
                p_value=item.p_value,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
            )
            for item in result.univariate_coefficients
        ],
        coefficients=[
            LogisticRegressionCoefficient(
                term=item.term,
                coefficient=item.coefficient,
                odds_ratio=item.odds_ratio,
                std_error=item.std_error,
                z_value=item.z_value,
                p_value=item.p_value,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
            )
            for item in result.coefficients
        ],
        plots=[
            LassoPlotPayload(
                name=plot.name,
                filename=plot.filename,
                media_type=plot.media_type,
                content_base64=plot.content_base64,
                vector_pdf_filename=plot.vector_pdf_filename,
                vector_pdf_base64=plot.vector_pdf_base64,
            )
            for plot in result.plots
        ],
        note=result.note,
    )


def _map_cox(result) -> CoxRegressionResponse:
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
        univariate_coefficients=[
            CoxRegressionCoefficient(
                term=item.term,
                coefficient=item.coefficient,
                hazard_ratio=item.hazard_ratio,
                std_error=item.std_error,
                z_value=item.z_value,
                p_value=item.p_value,
                conf_low=item.conf_low,
                conf_high=item.conf_high,
            )
            for item in result.univariate_coefficients
        ],
        coefficients=[
            CoxRegressionCoefficient(
                term=item.term,
                coefficient=item.coefficient,
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
        plots=[
            LassoPlotPayload(
                name=plot.name,
                filename=plot.filename,
                media_type=plot.media_type,
                content_base64=plot.content_base64,
                vector_pdf_filename=plot.vector_pdf_filename,
                vector_pdf_base64=plot.vector_pdf_base64,
            )
            for plot in result.plots
        ],
    )


def _map_pipeline_result(dataset_id: str, result: ClinicalPipelineExecutionResult) -> ClinicalPipelineRunResponse:
    return ClinicalPipelineRunResponse(
        run_id=result.run_id,
        template_kind=result.template_kind,
        dataset_id=dataset_id,
        dataset_state=ClinicalPipelineDatasetState(
            dataset_name=result.dataset_state.dataset_name,
            original_rows=result.dataset_state.original_rows,
            original_columns=result.dataset_state.original_columns,
            analysis_rows=result.dataset_state.analysis_rows,
            analysis_columns=result.dataset_state.analysis_columns,
            cleaning_operations=result.dataset_state.cleaning_operations,
            summary=_map_summary(result.dataset_state.summary),
        ),
        final_predictors=result.final_predictors,
        node_results=[
            ClinicalPipelineNodeResult(
                node_id=item.node_id,
                module_id=item.module_id,
                label=item.label,
                stage_id=item.stage_id,
                status=item.status,
                message=item.message,
                details=item.details,
                input_snapshot=item.input_snapshot,
                output_summary=item.output_summary,
                output_tables=item.output_tables,
                output_plots=item.output_plots,
                artifacts=[
                    ClinicalPipelineArtifactResult(
                        id=artifact.get("id"),
                        artifact_type=artifact.get("artifact_type", "result"),
                        name=artifact.get("name", "artifact"),
                        filename=artifact.get("filename"),
                        media_type=artifact.get("media_type"),
                        storage_key=artifact.get("storage_key"),
                        payload=artifact.get("payload") or {},
                    )
                    for artifact in item.artifacts
                ],
                logs=item.logs,
                next_dataset_ref=item.next_dataset_ref,
                next_variable_set=item.next_variable_set,
            )
            for item in result.node_results
        ],
        logs=result.logs,
        engine_notes=result.engine_notes,
        lasso_result=_map_lasso(result.lasso_result) if result.lasso_result else None,
        logistic_result=_map_logistic(result.logistic_result) if result.logistic_result else None,
        cox_result=_map_cox(result.cox_result) if result.cox_result else None,
    )


def _map_persisted_run_detail(run: WorkflowRun) -> ClinicalPipelineRunDetailResponse:
    dataset_state = run.dataset_state or {}
    summary = dataset_state.get("summary") or {}
    return ClinicalPipelineRunDetailResponse(
        run_id=str(run.id),
        project_id=str(run.project_id),
        workflow_id=str(run.workflow_id) if run.workflow_id else None,
        template_kind=run.template_kind,  # type: ignore[arg-type]
        dataset_id=str(run.dataset_id),
        status=run.status,
        created_at=_utc_isoformat(run.created_at) or "",
        completed_at=_utc_isoformat(run.completed_at),
        request_payload=run.request_payload or {},
        dataset_state=ClinicalPipelineDatasetState(
            dataset_name=dataset_state.get("dataset_name", ""),
            original_rows=dataset_state.get("original_rows", 0),
            original_columns=dataset_state.get("original_columns", 0),
            analysis_rows=dataset_state.get("analysis_rows", 0),
            analysis_columns=dataset_state.get("analysis_columns", 0),
            cleaning_operations=dataset_state.get("cleaning_operations") or [],
            summary=DatasetSummaryResponse.model_validate(summary or {}),
        ),
        final_predictors=run.final_predictors or [],
        node_results=[],
        logs=run.logs or [],
        engine_notes=run.engine_notes or [],
        lasso_result=None,
        logistic_result=None,
        cox_result=None,
    )


def _map_run_summary(run: WorkflowRun) -> ClinicalPipelineRunSummaryResponse:
    return ClinicalPipelineRunSummaryResponse(
        run_id=str(run.id),
        project_id=str(run.project_id),
        dataset_id=str(run.dataset_id),
        workflow_id=str(run.workflow_id) if run.workflow_id else None,
        template_kind=run.template_kind,  # type: ignore[arg-type]
        status=run.status,
        final_predictor_count=len(run.final_predictors or []),
        node_count=run.node_count,
        artifact_count=run.artifact_count,
        created_at=_utc_isoformat(run.created_at) or "",
        completed_at=_utc_isoformat(run.completed_at),
    )


def _map_run_node_detail(node: WorkflowRunNode, run_id: uuid.UUID, artifacts: list[WorkflowArtifact]) -> ClinicalPipelineNodeDetailResponse:
    return ClinicalPipelineNodeDetailResponse(
        run_id=str(run_id),
        node_id=node.node_id,
        module_id=node.module_id,
        label=node.label,
        stage_id=node.stage_id,
        status=node.status,  # type: ignore[arg-type]
        message=node.message,
        details=node.details or [],
        input_snapshot=node.input_snapshot or {},
        output_summary=node.output_summary or {},
        output_tables=node.output_tables or [],
        output_plots=node.output_plots or [],
        artifacts=[
            ClinicalPipelineArtifactResult(
                id=str(artifact.id),
                artifact_type=artifact.artifact_type,
                name=artifact.name,
                filename=artifact.filename,
                media_type=artifact.media_type,
                storage_key=artifact.storage_key,
                payload=artifact.payload or {},
            )
            for artifact in artifacts
        ],
        logs=node.logs or [],
        next_dataset_ref=node.next_dataset_ref,
        next_variable_set=node.next_variable_set or [],
        execution_order=node.execution_order,
        created_at=_utc_isoformat(node.created_at) or "",
    )


@router.post("/clinical-pipeline/run", response_model=ClinicalPipelineRunResponse)
async def run_clinical_pipeline(
    payload: ClinicalPipelineRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_uuid = uuid.UUID(payload.dataset_id)
        project_uuid = uuid.UUID(payload.project_id)
        workflow_uuid = uuid.UUID(payload.workflow_id) if payload.workflow_id else None
    except ValueError as exc:
        raise BadRequest("项目或数据集标识无效") from exc

    dataset = await _get_dataset_for_user(dataset_uuid, current_user, db)
    if dataset.project_id != project_uuid:
        raise BadRequest("所选数据集与当前项目不匹配")
    _validate_or_raise(payload.workflow_nodes, payload.workflow_connections)

    content = await storage_service.download(dataset.file_path)
    ext = f".{(dataset.file_format or '').lower()}".strip()
    kind_overrides = await get_dataset_kind_overrides(db, str(dataset.id))

    result = run_clinical_prediction_pipeline(
        content=content,
        ext=ext,
        dataset_name=dataset.name,
        template_kind=payload.template_kind,
        outcome_variable=payload.outcome_variable,
        time_variable=payload.time_variable,
        event_variable=payload.event_variable,
        predictor_variables=payload.predictor_variables,
        alpha=payload.alpha,
        nfolds=payload.nfolds,
        workflow_nodes=payload.workflow_nodes,
        workflow_connections=payload.workflow_connections,
        predictor_kind_overrides=kind_overrides,
        skip_completed=payload.skip_completed,
        dataset_id=payload.dataset_id,
        workflow_id=payload.workflow_id,
    )
    await persist_clinical_pipeline_run(
        db=db,
        owner_id=current_user.id,
        project_id=project_uuid,
        dataset_id=dataset_uuid,
        workflow_id=workflow_uuid,
        request_payload=payload.model_dump(),
        result=result,
    )
    return _map_pipeline_result(str(dataset.id), result)


@router.get("/runs/{run_id}", response_model=ClinicalPipelineRunDetailResponse)
async def get_clinical_pipeline_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run = await _get_run_for_user(run_id, current_user, db)
    response = _map_persisted_run_detail(run)

    node_result = await db.execute(
        select(WorkflowRunNode)
        .where(WorkflowRunNode.run_id == run.id)
        .order_by(WorkflowRunNode.execution_order.asc())
    )
    nodes = node_result.scalars().all()
    artifact_result = await db.execute(select(WorkflowArtifact).where(WorkflowArtifact.run_id == run.id))
    artifacts = artifact_result.scalars().all()
    artifact_map: dict[str, list[WorkflowArtifact]] = {}
    for artifact in artifacts:
        if artifact.run_node_id is None:
            continue
        artifact_map.setdefault(str(artifact.run_node_id), []).append(artifact)

    response.node_results = [
        ClinicalPipelineNodeResult(
            **_map_run_node_detail(node, run.id, artifact_map.get(str(node.id), [])).model_dump(
                exclude={"run_id", "execution_order"}
            )
        )
        for node in nodes
    ]
    return response


@router.get("/runs", response_model=list[ClinicalPipelineRunSummaryResponse])
async def list_clinical_pipeline_runs(
    project_id: str,
    workflow_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = uuid.UUID(project_id)
        workflow_uuid = uuid.UUID(workflow_id) if workflow_id else None
    except ValueError as exc:
        raise BadRequest("项目或流程标识无效") from exc

    await _get_project_for_user(project_uuid, current_user, db)
    query = (
        select(WorkflowRun)
        .where(WorkflowRun.project_id == project_uuid, WorkflowRun.owner_id == current_user.id)
        .order_by(WorkflowRun.created_at.desc())
    )
    if workflow_uuid:
        query = query.where(WorkflowRun.workflow_id == workflow_uuid)
    result = await db.execute(query)
    return [_map_run_summary(item) for item in result.scalars().all()]


@router.get("/runs/{run_id}/nodes/{node_id}", response_model=ClinicalPipelineNodeDetailResponse)
async def get_clinical_pipeline_run_node(
    run_id: uuid.UUID,
    node_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run = await _get_run_for_user(run_id, current_user, db)
    result = await db.execute(
        select(WorkflowRunNode)
        .where(WorkflowRunNode.run_id == run.id, WorkflowRunNode.node_id == node_id)
        .limit(1)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise NotFound("节点运行结果不存在")

    artifact_result = await db.execute(select(WorkflowArtifact).where(WorkflowArtifact.run_node_id == node.id))
    artifacts = artifact_result.scalars().all()
    return _map_run_node_detail(node, run.id, artifacts)


@router.get("/artifacts/{artifact_id}/download")
async def download_clinical_pipeline_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artifact = await _get_artifact_for_user(artifact_id, current_user, db)

    if artifact.storage_key:
        content = await storage_service.download(artifact.storage_key)
    else:
        payload = artifact.payload or {}
        content_base64 = payload.get("content_base64")
        if not content_base64:
            raise NotFound("当前产物没有可下载的文件内容")
        try:
            content = base64.b64decode(content_base64)
        except Exception as exc:
            raise BadRequest("产物内容损坏，无法下载") from exc

    filename = artifact.filename or f"{artifact.name}.bin"
    media_type = artifact.media_type or "application/octet-stream"
    is_csv = filename.lower().endswith(".csv") or media_type.lower().startswith("text/csv")
    if is_csv and not content.startswith(b"\xef\xbb\xbf"):
        content = b"\xef\xbb\xbf" + content
        media_type = "text/csv; charset=utf-8"
    headers = {
        "Content-Disposition": _build_content_disposition(filename),
    }
    return Response(content=content, media_type=media_type, headers=headers)
