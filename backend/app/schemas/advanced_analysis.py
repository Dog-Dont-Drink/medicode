"""Schemas for advanced clinical modeling pipelines."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.dataset import DatasetSummaryResponse
from app.schemas.descriptive import (
    CoxRegressionResponse,
    LassoRegressionResponse,
    LogisticRegressionResponse,
)


class WorkflowNodeRequest(BaseModel):
    id: str
    module_id: str
    label: str
    stage_id: str
    values: dict[str, str] = Field(default_factory=dict)


class SavedWorkflowConnection(BaseModel):
    id: str
    from_node_id: str
    to_node_id: str
    output_port_id: str | None = None


class ClinicalPipelineRunRequest(BaseModel):
    project_id: str
    dataset_id: str
    workflow_id: str | None = None
    template_kind: Literal["binary", "survival"]
    outcome_variable: str | None = None
    time_variable: str | None = None
    event_variable: str | None = None
    predictor_variables: list[str] = Field(default_factory=list)
    alpha: float = Field(default=0.05, gt=0, lt=0.2)
    nfolds: int = Field(default=10, ge=3, le=20)
    workflow_nodes: list[WorkflowNodeRequest] = Field(default_factory=list)
    workflow_connections: list[SavedWorkflowConnection] = Field(default_factory=list)
    skip_completed: bool = False


class ClinicalPipelineArtifactResult(BaseModel):
    id: str | None = None
    artifact_type: str
    name: str
    filename: str | None = None
    media_type: str | None = None
    storage_key: str | None = None
    payload: dict = Field(default_factory=dict)


class ClinicalPipelineNodeResult(BaseModel):
    node_id: str
    module_id: str
    label: str
    stage_id: str
    status: Literal["completed", "configured", "unsupported", "skipped", "failed"]
    message: str
    details: list[str] = Field(default_factory=list)
    input_snapshot: dict = Field(default_factory=dict)
    output_summary: dict = Field(default_factory=dict)
    output_tables: list[dict] = Field(default_factory=list)
    output_plots: list[dict] = Field(default_factory=list)
    artifacts: list[ClinicalPipelineArtifactResult] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    next_dataset_ref: str | None = None
    next_variable_set: list[str] = Field(default_factory=list)
    created_at: str | None = None


class ClinicalPipelineDatasetState(BaseModel):
    dataset_name: str
    original_rows: int
    original_columns: int
    analysis_rows: int
    analysis_columns: int
    cleaning_operations: list[str] = Field(default_factory=list)
    summary: DatasetSummaryResponse


class ClinicalPipelineRunResponse(BaseModel):
    run_id: str | None = None
    template_kind: Literal["binary", "survival", "continuous"]
    dataset_id: str
    dataset_state: ClinicalPipelineDatasetState
    final_predictors: list[str] = Field(default_factory=list)
    node_results: list[ClinicalPipelineNodeResult] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    engine_notes: list[str] = Field(default_factory=list)
    lasso_result: LassoRegressionResponse | None = None
    logistic_result: LogisticRegressionResponse | None = None
    cox_result: CoxRegressionResponse | None = None


class ClinicalPipelineRunDetailResponse(ClinicalPipelineRunResponse):
    project_id: str
    workflow_id: str | None = None
    status: str
    created_at: str
    completed_at: str | None = None
    request_payload: dict = Field(default_factory=dict)


class ClinicalPipelineRunSummaryResponse(BaseModel):
    run_id: str
    project_id: str
    dataset_id: str
    workflow_id: str | None = None
    template_kind: Literal["binary", "survival", "continuous"]
    status: str
    final_predictor_count: int
    node_count: int
    artifact_count: int
    created_at: str
    completed_at: str | None = None


class ClinicalPipelineNodeDetailResponse(ClinicalPipelineNodeResult):
    run_id: str
    execution_order: int
    created_at: str
