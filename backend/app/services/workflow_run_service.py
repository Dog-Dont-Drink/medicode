"""Persistence helpers for clinical workflow execution runs."""

from __future__ import annotations

import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workflow_run import WorkflowArtifact, WorkflowRun, WorkflowRunNode
from app.services.advanced_modeling_service import ClinicalPipelineExecutionResult
from app.services.dataset_parser import DatasetSummary


def _to_json_compatible(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(key): _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_compatible(item) for item in value]
    if is_dataclass(value):
        return _to_json_compatible(asdict(value))
    return value


def _serialize_dataset_summary(summary: DatasetSummary) -> dict:
    return {
        "total_rows": summary.total_rows,
        "total_columns": summary.total_columns,
        "numeric_columns": summary.numeric_columns,
        "categorical_columns": summary.categorical_columns,
        "datetime_columns": summary.datetime_columns,
        "boolean_columns": summary.boolean_columns,
        "complete_rows": summary.complete_rows,
        "duplicate_rows": summary.duplicate_rows,
        "missing_cells": summary.missing_cells,
        "missing_rate": summary.missing_rate,
        "columns": [
            {
                "name": column.name,
                "kind": column.kind,
                "kind_source": column.kind_source,
                "non_null_count": column.non_null_count,
                "missing_count": column.missing_count,
                "missing_rate": column.missing_rate,
                "unique_count": column.unique_count,
                "sample_values": column.sample_values,
                "numeric_min": column.numeric_min,
                "numeric_max": column.numeric_max,
                "numeric_mean": column.numeric_mean,
                "numeric_std": column.numeric_std,
                "numeric_median": column.numeric_median,
                "numeric_q1": column.numeric_q1,
                "numeric_q3": column.numeric_q3,
                "datetime_min": column.datetime_min,
                "datetime_max": column.datetime_max,
                "top_values": [
                    {
                        "value": item.value,
                        "count": item.count,
                        "ratio": item.ratio,
                    }
                    for item in (column.top_values or [])
                ],
            }
            for column in summary.columns
        ],
    }


async def persist_clinical_pipeline_run(
    *,
    db: AsyncSession,
    owner_id: uuid.UUID,
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    workflow_id: uuid.UUID | None,
    request_payload: dict[str, Any],
    result: ClinicalPipelineExecutionResult,
) -> WorkflowRun:
    run = WorkflowRun(
        project_id=project_id,
        dataset_id=dataset_id,
        workflow_id=workflow_id,
        owner_id=owner_id,
        template_kind=result.template_kind,
        status="completed",
        request_payload=_to_json_compatible(request_payload),
        dataset_state={
            "dataset_name": result.dataset_state.dataset_name,
            "original_rows": result.dataset_state.original_rows,
            "original_columns": result.dataset_state.original_columns,
            "analysis_rows": result.dataset_state.analysis_rows,
            "analysis_columns": result.dataset_state.analysis_columns,
            "cleaning_operations": result.dataset_state.cleaning_operations,
            "summary": _serialize_dataset_summary(result.dataset_state.summary),
        },
        final_predictors=_to_json_compatible(result.final_predictors),
        logs=_to_json_compatible(result.logs),
        engine_notes=_to_json_compatible(result.engine_notes),
        node_count=len(result.node_results),
        artifact_count=0,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    artifact_count = 0
    for index, node in enumerate(result.node_results, start=1):
        run_node = WorkflowRunNode(
            run_id=run.id,
            node_id=node.node_id,
            module_id=node.module_id,
            label=node.label,
            stage_id=node.stage_id,
            status=node.status,
            message=node.message,
            details=_to_json_compatible(node.details),
            input_snapshot=_to_json_compatible(node.input_snapshot),
            output_summary=_to_json_compatible(node.output_summary),
            output_tables=_to_json_compatible(node.output_tables),
            output_plots=_to_json_compatible(node.output_plots),
            logs=_to_json_compatible(node.logs),
            next_dataset_ref=node.next_dataset_ref,
            next_variable_set=_to_json_compatible(node.next_variable_set),
            execution_order=index,
        )
        db.add(run_node)
        await db.flush()

        node_artifacts = list(node.artifacts or [])
        if not node_artifacts and node.output_plots:
            node_artifacts = [
                {
                    "artifact_type": "plot",
                    "name": plot.get("name") or "plot",
                    "filename": plot.get("filename"),
                    "media_type": plot.get("media_type"),
                    "storage_key": None,
                    "payload": plot,
                }
                for plot in node.output_plots
            ]

        persisted_artifacts: list[dict] = []
        for artifact in node_artifacts:
            record = WorkflowArtifact(
                run_id=run.id,
                run_node_id=run_node.id,
                owner_id=owner_id,
                artifact_type=str(artifact.get("artifact_type") or "result"),
                name=str(artifact.get("name") or "artifact"),
                filename=artifact.get("filename"),
                media_type=artifact.get("media_type"),
                storage_key=artifact.get("storage_key"),
                payload=_to_json_compatible(artifact.get("payload") or {}),
            )
            db.add(record)
            await db.flush()
            artifact_count += 1
            persisted_artifacts.append(
                {
                    "id": str(record.id),
                    "artifact_type": record.artifact_type,
                    "name": record.name,
                    "filename": record.filename,
                    "media_type": record.media_type,
                    "storage_key": record.storage_key,
                    "payload": record.payload,
                }
            )
        node.artifacts = persisted_artifacts

    run.artifact_count = artifact_count
    result.run_id = str(run.id)
    return run
