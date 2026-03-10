"""Orchestration service for advanced clinical modeling pipelines."""

from __future__ import annotations

import base64
import hashlib
import json as _json
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from app.core.exceptions import BadRequest
from app.schemas.advanced_analysis import SavedWorkflowConnection, WorkflowNodeRequest
from app.services.dataset_parser import (
    DatasetSummary,
    dataframe_to_csv_bytes,
    infer_dataframe_column_kinds,
    load_tabular_dataframe,
    summarize_tabular_content,
)
from app.services.regression_service import (
    BinaryModelMetricData,
    BootstrapValidationExecutionResult,
    BorutaSelectionExecutionResult,
    CalibrationValidationExecutionResult,
    CoxRegressionExecutionResult,
    DcaValidationExecutionResult,
    LassoRegressionExecutionResult,
    LogisticRegressionExecutionResult,
    NomogramExecutionResult,
    RocValidationExecutionResult,
    RandomForestSelectionExecutionResult,
    TreeModelExecutionResult,
    UnivariateScreenExecutionResult,
    run_bootstrap_validation,
    run_boruta_selection,
    run_calibration_validation,
    run_cox_regression,
    run_dca_validation,
    run_lasso_regression,
    run_logistic_regression,
    run_missing_value_processing,
    run_nomogram_plot,
    run_random_forest_importance_selection,
    run_random_forest_model,
    run_roc_validation,
    run_univariate_cox_screen,
    run_univariate_logistic_screen,
    run_xgboost_model,
)
from app.services.tableone_service import generate_tableone


@dataclass
class PipelineNodeStatusData:
    node_id: str
    module_id: str
    label: str
    stage_id: str
    status: Literal["completed", "configured", "unsupported", "skipped", "failed"]
    message: str
    details: list[str] = field(default_factory=list)
    input_snapshot: dict = field(default_factory=dict)
    output_summary: dict = field(default_factory=dict)
    output_tables: list[dict] = field(default_factory=list)
    output_plots: list[dict] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    next_dataset_ref: str | None = None
    next_variable_set: list[str] = field(default_factory=list)


@dataclass
class ClinicalPipelineDatasetStateData:
    dataset_name: str
    original_rows: int
    original_columns: int
    analysis_rows: int
    analysis_columns: int
    cleaning_operations: list[str]
    summary: DatasetSummary


@dataclass
class ClinicalPipelineExecutionResult:
    template_kind: Literal["binary", "survival"]
    dataset_state: ClinicalPipelineDatasetStateData
    run_id: str | None = None
    final_predictors: list[str] = field(default_factory=list)
    node_results: list[PipelineNodeStatusData] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    engine_notes: list[str] = field(default_factory=list)
    lasso_result: LassoRegressionExecutionResult | None = None
    logistic_result: LogisticRegressionExecutionResult | None = None
    cox_result: CoxRegressionExecutionResult | None = None
    random_forest_model_result: TreeModelExecutionResult | None = None
    xgboost_model_result: TreeModelExecutionResult | None = None


@dataclass
class PipelineExecutionContext:
    df: pd.DataFrame
    predictors: list[str]
    kind_overrides: dict[str, str] = field(default_factory=dict)
    holdout_frames: dict[str, pd.DataFrame] = field(default_factory=dict)
    lasso_result: LassoRegressionExecutionResult | None = None
    logistic_result: LogisticRegressionExecutionResult | None = None
    cox_result: CoxRegressionExecutionResult | None = None
    random_forest_model_result: TreeModelExecutionResult | None = None
    xgboost_model_result: TreeModelExecutionResult | None = None
    univariate_result: UnivariateScreenExecutionResult | None = None


STAGE_ORDER = {
    "data-preparation": 0,
    "feature-processing": 1,
    "model-development": 2,
    "model-validation": 3,
}


# ---------------------------------------------------------------------------
# In-memory pipeline execution cache for incremental runs
# ---------------------------------------------------------------------------
# Key: "{dataset_id}:{workflow_id}" → per-node cached (config_hash, context, node_result)
_pipeline_run_cache: dict[str, dict[str, tuple[str, PipelineExecutionContext, PipelineNodeStatusData]]] = {}

_NODE_EXECUTION_VERSIONS: dict[str, str] = {
    "calibration": "2026-03-10-fix-val-prob-main",
}


def _node_config_hash(node: WorkflowNodeRequest) -> str:
    """Deterministic hash of a node's module_id + values for cache invalidation."""
    raw = _json.dumps(
        {
            "m": node.module_id,
            "v": dict(node.values),
            "exec_version": _NODE_EXECUTION_VERSIONS.get(node.module_id, "v1"),
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.md5(raw.encode()).hexdigest()


def _clean_str_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _required_columns(
    df: pd.DataFrame,
    workflow_nodes: list[WorkflowNodeRequest],
    template_kind: Literal["binary", "survival"],
    outcome_variable: str | None,
    time_variable: str | None,
    event_variable: str | None,
    predictor_variables: list[str],
) -> list[str]:
    active_modules = {node.module_id for node in workflow_nodes}
    predictors = _clean_str_list(predictor_variables)
    split_runtime_columns = _clean_str_list(
        [
            *[
                str(node.values.get("stratifyField", "")).strip()
                for node in workflow_nodes
                if node.module_id == "split" and str(node.values.get("sampling", "")).strip() == "分层抽样"
            ],
            *[
                str(node.values.get("timeSplitField", "")).strip()
                for node in workflow_nodes
                if node.module_id == "split" and str(node.values.get("sampling", "")).strip() == "时间切分"
            ],
        ]
    )

    data_only_modules = {"field-mapping", "missing-value", "split", "encoding"}
    requires_predictors = any(module_id not in data_only_modules for module_id in active_modules)

    if not predictors and not requires_predictors:
        return list(df.columns)

    if not predictors and requires_predictors:
        raise BadRequest("请至少选择一个预测变量")

    if template_kind == "binary" and any(
        module_id in {"univariate-screen", "lasso-selection", "rf-importance", "boruta-selection", "logistic-model", "xgboost", "random-forest", "roc", "calibration", "dca", "nomogram"}
        for module_id in active_modules
    ):
        if not outcome_variable:
            raise BadRequest("二分类模板需要指定结局变量")
        return _clean_str_list([outcome_variable, *predictors, *split_runtime_columns])

    if template_kind == "survival" and any(
        module_id in {"univariate-screen", "cox-model", "bootstrap", "nomogram"}
        for module_id in active_modules
    ):
        if not time_variable or not event_variable:
            raise BadRequest("生存模板需要同时指定生存时间变量和结局事件变量")
        return _clean_str_list([time_variable, event_variable, *predictors, *split_runtime_columns])

    required = [outcome_variable, time_variable, event_variable, *predictors, *split_runtime_columns]
    cleaned = _clean_str_list([item for item in required if item])
    return cleaned or list(df.columns)


def _validate_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise BadRequest(f"数据集中缺少以下变量: {', '.join(missing)}")


def _supports_binary_outcome(series: pd.Series) -> bool:
    non_null = series.dropna()
    if non_null.empty:
        return False
    if pd.api.types.is_bool_dtype(non_null):
        return True
    if pd.api.types.is_numeric_dtype(non_null):
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        unique_values = sorted(float(item) for item in pd.unique(numeric))
        return len(unique_values) == 2
    return int(non_null.astype(str).nunique(dropna=True)) == 2


def _node_map(workflow_nodes: list[WorkflowNodeRequest]) -> dict[str, WorkflowNodeRequest]:
    return {node.module_id: node for node in workflow_nodes}


def _node_id_map(workflow_nodes: list[WorkflowNodeRequest]) -> dict[str, WorkflowNodeRequest]:
    return {node.id: node for node in workflow_nodes}


def _incoming_connection_map(
    workflow_nodes: list[WorkflowNodeRequest],
    workflow_connections: list[SavedWorkflowConnection],
) -> dict[str, list[SavedWorkflowConnection]]:
    node_ids = {node.id for node in workflow_nodes}
    incoming: dict[str, list[SavedWorkflowConnection]] = {node.id: [] for node in workflow_nodes}
    for connection in workflow_connections:
        if connection.from_node_id not in node_ids or connection.to_node_id not in node_ids:
            continue
        incoming.setdefault(connection.to_node_id, []).append(connection)
    return incoming


def _topological_nodes(
    workflow_nodes: list[WorkflowNodeRequest],
    workflow_connections: list[SavedWorkflowConnection],
) -> list[WorkflowNodeRequest]:
    node_lookup = _node_id_map(workflow_nodes)
    incoming_map = _incoming_connection_map(workflow_nodes, workflow_connections)
    outgoing_map: dict[str, list[str]] = {node.id: [] for node in workflow_nodes}
    indegree: dict[str, int] = {node.id: 0 for node in workflow_nodes}

    for connection in workflow_connections:
        if connection.from_node_id not in node_lookup or connection.to_node_id not in node_lookup:
            continue
        outgoing_map[connection.from_node_id].append(connection.to_node_id)
        indegree[connection.to_node_id] += 1

    queue = sorted(
        [node for node in workflow_nodes if indegree[node.id] == 0],
        key=lambda item: (STAGE_ORDER.get(item.stage_id, 99), item.id),
    )
    ordered: list[WorkflowNodeRequest] = []

    while queue:
        node = queue.pop(0)
        ordered.append(node)
        for target_id in outgoing_map.get(node.id, []):
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                queue.append(node_lookup[target_id])
        queue.sort(key=lambda item: (STAGE_ORDER.get(item.stage_id, 99), item.id))

    if len(ordered) == len(workflow_nodes):
        return ordered

    remaining = [node for node in workflow_nodes if node.id not in {item.id for item in ordered}]
    remaining.sort(key=lambda item: (STAGE_ORDER.get(item.stage_id, 99), item.id))
    return [*ordered, *remaining]


def _append_node_result(
    container: list[PipelineNodeStatusData],
    node: WorkflowNodeRequest | None,
    status: Literal["completed", "configured", "unsupported", "skipped", "failed"],
    message: str,
    details: list[str] | None = None,
) -> None:
    if node is None:
        return
    container.append(
        PipelineNodeStatusData(
            node_id=node.id,
            module_id=node.module_id,
            label=node.label,
            stage_id=node.stage_id,
            status=status,
            message=message,
            details=details or [],
        )
    )


def _summarize_dataframe(df: pd.DataFrame, kind_overrides: dict[str, str] | None = None) -> DatasetSummary:
    content = dataframe_to_csv_bytes(df)
    return summarize_tabular_content(content, ".csv", kind_overrides=kind_overrides)


def _apply_missing_value_node(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    analysis_columns: list[str],
    node: WorkflowNodeRequest | None,
    outcome_variable: str | None,
    time_variable: str | None,
    event_variable: str | None,
    predictors: list[str],
) -> tuple[pd.DataFrame, list[str], list[str], PipelineNodeStatusData | None]:
    if node is None:
        return df, [], predictors, None

    runtime_analysis_columns = _clean_str_list(
        [
            *[column for column in analysis_columns if column in df.columns],
            *[column for column in predictors if column in df.columns],
            *[item for item in [outcome_variable, time_variable, event_variable] if item and item in df.columns],
        ]
    )
    if not runtime_analysis_columns:
        runtime_analysis_columns = list(df.columns)

    method = (node.values.get("method") or "多重插补").strip()
    threshold_raw = str(node.values.get("threshold") or "0.20").strip()
    try:
        threshold = float(threshold_raw)
    except ValueError as exc:
        raise BadRequest("缺失比例阈值必须是有效数字") from exc

    result = run_missing_value_processing(
        df=df,
        dataset_name=dataset_name,
        analysis_columns=runtime_analysis_columns,
        method=method,
        threshold=threshold,
        protected_columns=[item for item in [outcome_variable, time_variable, event_variable] if item],
    )
    next_predictors = [column for column in predictors if column in result.cleaned_df.columns]
    node_result = PipelineNodeStatusData(
        node_id=node.id,
        module_id=node.module_id,
        label=node.label,
        stage_id=node.stage_id,
        status="completed",
        message=f"{result.method}已执行",
        details=result.operations,
        output_tables=[
            {
                "name": "missing_value_summary",
                "columns": ["metric", "value"],
                "rows": [
                    ["method", result.method],
                    ["threshold", result.threshold],
                    ["input_rows", result.input_rows],
                    ["output_rows", result.output_rows],
                    ["removed_rows", result.removed_rows],
                    ["removed_columns", result.removed_columns],
                    ["numeric_imputed_cells", result.numeric_imputed_cells],
                    ["categorical_imputed_cells", result.categorical_imputed_cells],
                    ["missing_cells_before", result.missing_cells_before],
                    ["missing_cells_after", result.missing_cells_after],
                ],
            },
            {
                "name": "missing_value_removed_columns",
                "columns": ["removed_column"],
                "rows": [[column] for column in result.removed_column_names],
            },
        ],
        artifacts=[
            _artifact_from_bytes(
                artifact_type="dataset",
                name="缺失值处理后数据",
                filename=result.output_name,
                media_type="text/csv",
                content=result.csv_content,
            )
        ],
        logs=result.operations,
        next_dataset_ref=f"inmemory://{node.id}/cleaned_dataset",
        next_variable_set=next_predictors,
    )
    return result.cleaned_df, result.operations, next_predictors, node_result


def _encoding_target_series(
    df: pd.DataFrame,
    *,
    template_kind: Literal["binary", "survival"],
    outcome_variable: str | None,
    event_variable: str | None,
) -> tuple[pd.Series, str, str | None]:
    target_column = outcome_variable if template_kind == "binary" else event_variable
    if not target_column or target_column not in df.columns:
        raise BadRequest("目标编码需要可用的结局变量")

    raw_target = df[target_column]
    numeric_target = pd.to_numeric(raw_target, errors="coerce")
    if not numeric_target.dropna().empty:
        return numeric_target.astype(float), target_column, None

    non_null = raw_target.dropna()
    unique_values = pd.unique(non_null)
    if unique_values.size != 2:
        raise BadRequest("目标编码当前仅支持二分类结局/事件变量")

    ordered_levels = sorted((str(item) for item in unique_values))
    positive_level = ordered_levels[-1]
    encoded = raw_target.map(lambda value: 1.0 if str(value) == positive_level else (0.0 if pd.notna(value) else np.nan))
    return encoded.astype(float), target_column, positive_level


def _categorical_predictors_for_encoding(
    df: pd.DataFrame,
    predictors: list[str],
    kind_overrides: dict[str, str] | None,
) -> list[str]:
    kind_map = infer_dataframe_column_kinds(df, kind_overrides)
    return [
        column
        for column in predictors
        if column in df.columns and kind_map.get(column, ("categorical", "auto"))[0] in {"categorical", "boolean"}
    ]


def _replace_predictors(
    predictors: list[str],
    replacements: dict[str, list[str]],
) -> list[str]:
    next_predictors: list[str] = []
    for predictor in predictors:
        if predictor in replacements:
            next_predictors.extend(replacements[predictor])
        else:
            next_predictors.append(predictor)
    return _clean_str_list(next_predictors)


def _binary_encoding_payload(series: pd.Series) -> tuple[pd.Series, list[list[object]], str]:
    non_null = series.dropna()
    unique_values = pd.unique(non_null)
    if unique_values.size != 2:
        raise BadRequest("二分类编码仅支持恰好两个非空取值的变量")

    if pd.api.types.is_bool_dtype(series):
        encoded = series.astype("boolean").astype("Int64")
        return encoded, [[str(False), 0], [str(True), 1]], "converted"

    numeric_series = pd.to_numeric(series, errors="coerce")
    numeric_non_null = numeric_series.dropna()
    if numeric_non_null.shape[0] == non_null.shape[0]:
        unique_numeric = sorted(float(item) for item in pd.unique(numeric_non_null))
        if len(unique_numeric) == 2 and np.isclose(unique_numeric, [0.0, 1.0]).all():
            return numeric_series.astype("Int64"), [[0, 0], [1, 1]], "kept"

    ordered_levels = sorted((str(item) for item in unique_values))
    level_to_code = {level: index for index, level in enumerate(ordered_levels)}
    encoded = series.map(lambda value: level_to_code.get(str(value)) if pd.notna(value) else pd.NA).astype("Int64")
    return encoded, [[level, code] for level, code in level_to_code.items()], "converted"


def _sorted_levels(series: pd.Series) -> list[object]:
    unique_values = [item for item in pd.unique(series.dropna())]
    return sorted(unique_values, key=lambda value: str(value))


def _apply_encoding_node(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    node: WorkflowNodeRequest | None,
    predictors: list[str],
    template_kind: Literal["binary", "survival"],
    outcome_variable: str | None,
    event_variable: str | None,
    kind_overrides: dict[str, str],
    holdout_frames: dict[str, pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, list[str], dict[str, str], dict[str, pd.DataFrame], PipelineNodeStatusData | None]:
    if node is None:
        return df, predictors, kind_overrides, dict(holdout_frames or {}), None

    strategy = str(node.values.get("encoding") or "One-hot").strip() or "One-hot"
    drop_first = (node.values.get("dropFirst") or "是") == "是"
    encoding_columns = _categorical_predictors_for_encoding(df, predictors, kind_overrides)

    if not encoding_columns:
        return (
            df,
            predictors,
            kind_overrides,
            dict(holdout_frames or {}),
            PipelineNodeStatusData(
                node_id=node.id,
                module_id=node.module_id,
                label=node.label,
                stage_id=node.stage_id,
                status="completed",
                message="当前预测变量中无可编码的分类变量",
                details=["本节点跳过数据改写，直接沿用上游变量集。"],
                input_snapshot={
                    "encoding": strategy,
                    "drop_first": drop_first,
                    "predictor_count": len(predictors),
                },
                output_summary={
                    "encoded_column_count": 0,
                    "predictor_count": len(predictors),
                },
                next_dataset_ref=f"inmemory://{node.id}/passthrough_dataset",
                next_variable_set=_clean_str_list(predictors),
            ),
        )

    next_df = df.copy()
    next_holdout_frames = {label: frame.copy() for label, frame in (holdout_frames or {}).items()}
    next_kind_overrides = dict(kind_overrides)
    output_tables: list[dict] = []
    details: list[str] = []
    predictor_replacements: dict[str, list[str]] = {}
    added_columns = 0
    target_reference_note: str | None = None

    if strategy == "One-hot":
        one_hot_columns: list[str] = []
        binary_mapping_rows: list[list[object]] = []
        binary_kept_columns: list[str] = []
        binary_converted_columns: list[str] = []

        for column in encoding_columns:
            unique_count = int(next_df[column].dropna().nunique(dropna=True))
            if unique_count >= 3:
                one_hot_columns.append(column)
                continue
            if unique_count == 2:
                encoded_series, mapping_rows, action = _binary_encoding_payload(next_df[column])
                next_df[column] = encoded_series
                mapping = {str(raw_value): encoded_value for _, raw_value, encoded_value, _ in [[column, *row, action] for row in mapping_rows]}
                for label, frame in next_holdout_frames.items():
                    frame[column] = frame[column].map(lambda value: mapping.get(str(value)) if pd.notna(value) else pd.NA).astype("Int64")
                    next_holdout_frames[label] = frame
                next_kind_overrides[column] = "numeric"
                predictor_replacements[column] = [column]
                if action == "kept":
                    binary_kept_columns.append(column)
                else:
                    binary_converted_columns.append(column)
                for raw_value, encoded_value in mapping_rows:
                    binary_mapping_rows.append([column, raw_value, encoded_value, action])
                continue

            predictor_replacements[column] = [column]
            details.append(f"{column} 仅有 {unique_count} 个非空取值，跳过 One-hot 展开。")

        if one_hot_columns:
            for column in one_hot_columns:
                levels = _sorted_levels(next_df[column])
                generated_levels = levels[1:] if drop_first and len(levels) >= 1 else levels
                generated: list[str] = []
                for level in generated_levels:
                    generated_column = f"{column}__{level}"
                    next_df[generated_column] = next_df[column].map(lambda value, current_level=level: int(pd.notna(value) and value == current_level)).astype("int64")
                    for label, frame in next_holdout_frames.items():
                        frame[generated_column] = frame[column].map(lambda value, current_level=level: int(pd.notna(value) and value == current_level)).astype("int64")
                        next_holdout_frames[label] = frame
                    generated.append(generated_column)
                next_df = next_df.drop(columns=[column])
                for label, frame in next_holdout_frames.items():
                    if column in frame.columns:
                        frame = frame.drop(columns=[column])
                    next_holdout_frames[label] = frame
                predictor_replacements[column] = generated
                added_columns += len(generated)
                next_kind_overrides.pop(column, None)
                for generated_column in generated:
                    next_kind_overrides[generated_column] = "numeric"

        details.append(
            f"One-hot 仅应用于 {len(one_hot_columns)} 个三分类及以上变量，新增 {added_columns} 列。"
        )
        if binary_kept_columns:
            details.append(f"{len(binary_kept_columns)} 个二分类变量已是 0/1，保留单列。")
        if binary_converted_columns:
            details.append(f"{len(binary_converted_columns)} 个二分类变量已改写为单列 0/1 编码。")
        output_tables.append(
            {
                "name": "encoding_columns",
                "columns": ["source_column", "mode", "generated_columns"],
                "rows": [
                    [
                        column,
                        "one_hot" if column in one_hot_columns else "binary_single" if column in binary_kept_columns or column in binary_converted_columns else "skipped",
                        ", ".join(predictor_replacements.get(column, [])) or "(kept)",
                    ]
                    for column in encoding_columns
                ],
            }
        )
        if binary_mapping_rows:
            output_tables.append(
                {
                    "name": "binary_encoding_mapping",
                    "columns": ["column", "raw_value", "encoded_value", "action"],
                    "rows": binary_mapping_rows,
                }
            )
    elif strategy == "标签编码":
        mapping_rows: list[list[object]] = []
        for column in encoding_columns:
            series = next_df[column]
            mapping: dict[tuple[str, str], int] = {}
            next_code = 0
            encoded_values: list[int] = []
            for value in series.tolist():
                if pd.isna(value):
                    encoded_values.append(-1)
                    continue
                key = (type(value).__name__, str(value))
                if key not in mapping:
                    mapping[key] = next_code
                    next_code += 1
                encoded_values.append(mapping[key])
            next_df[column] = pd.Series(encoded_values, index=series.index, dtype="int64")
            for label, frame in next_holdout_frames.items():
                frame[column] = frame[column].map(lambda value: mapping.get((type(value).__name__, str(value)), -1) if pd.notna(value) else -1).astype("int64")
                next_holdout_frames[label] = frame
            next_kind_overrides[column] = "numeric"
            predictor_replacements[column] = [column]
            for (_, display_value), code in mapping.items():
                mapping_rows.append([column, display_value, code])
        details.append(f"对 {len(encoding_columns)} 个分类预测变量执行标签编码，缺失值统一编码为 -1。")
        output_tables.append(
            {
                "name": "label_encoding_mapping",
                "columns": ["column", "category", "code"],
                "rows": mapping_rows,
            }
        )
    elif strategy == "目标编码":
        target_series, target_column, positive_level = _encoding_target_series(
            next_df,
            template_kind=template_kind,
            outcome_variable=outcome_variable,
            event_variable=event_variable,
        )
        mapping_rows: list[list[object]] = []
        for column in encoding_columns:
            frame = pd.DataFrame({"category": next_df[column], "__target__": target_series})
            stats = (
                frame.dropna(subset=["category", "__target__"])
                .groupby("category", dropna=True)["__target__"]
                .mean()
            )
            global_mean = float(target_series.dropna().mean()) if not target_series.dropna().empty else 0.0
            next_df[column] = next_df[column].map(stats).fillna(global_mean).astype(float)
            for label, frame in next_holdout_frames.items():
                frame[column] = frame[column].map(lambda value: stats.get(value, global_mean) if pd.notna(value) else global_mean).astype(float)
                next_holdout_frames[label] = frame
            next_kind_overrides[column] = "numeric"
            predictor_replacements[column] = [column]
            for category, mean_value in stats.items():
                mapping_rows.append([column, str(category), round(float(mean_value), 6)])
        target_reference_note = f"编码参照字段: {target_column}"
        if positive_level is not None:
            target_reference_note += f"（正类={positive_level}）"
        details.append(f"对 {len(encoding_columns)} 个分类预测变量执行目标编码，缺失类别回填全局均值。")
        details.append(target_reference_note)
        output_tables.append(
            {
                "name": "target_encoding_mapping",
                "columns": ["column", "category", "target_mean"],
                "rows": mapping_rows,
            }
        )
    else:
        raise BadRequest(f"不支持的编码方式: {strategy}")

    next_predictors = _replace_predictors(predictors, predictor_replacements)
    artifact_name = f"{dataset_name.rsplit('.', 1)[0]}_encoded.csv" if "." in dataset_name else f"{dataset_name}_encoded.csv"
    node_result = PipelineNodeStatusData(
        node_id=node.id,
        module_id=node.module_id,
        label=node.label,
        stage_id=node.stage_id,
        status="completed",
        message=f"{strategy}已执行，当前下游变量数为 {len(next_predictors)}",
        details=details,
        input_snapshot={
            "encoding": strategy,
            "drop_first": drop_first,
            "input_predictors": predictors,
            "encoding_columns": encoding_columns,
        },
        output_summary={
            "encoding_strategy": strategy,
            "drop_first": drop_first,
            "encoded_column_count": len(encoding_columns),
            "added_columns": added_columns,
            "one_hot_only_multiclass": strategy == "One-hot",
            "output_predictor_count": len(next_predictors),
        },
        output_tables=output_tables,
        artifacts=[
            _artifact_from_bytes(
                artifact_type="dataset",
                name="分类变量编码后数据",
                filename=artifact_name,
                media_type="text/csv",
                content=dataframe_to_csv_bytes(next_df),
            )
        ],
        logs=details,
        next_dataset_ref=f"inmemory://{node.id}/encoded_dataset",
        next_variable_set=next_predictors,
    )
    return next_df, next_predictors, next_kind_overrides, next_holdout_frames, node_result


def _extract_lasso_predictors(
    result: LassoRegressionExecutionResult,
    criterion: str,
) -> list[str]:
    use_lambda_min = criterion == "lambda.min"
    selected: list[str] = []
    for feature in result.selected_features:
        if use_lambda_min and feature.selected_at_lambda_min:
            selected.append(feature.term)
        elif not use_lambda_min and feature.selected_at_lambda_1se:
            selected.append(feature.term)
    return _clean_str_list(selected)


def _merge_predictors(contexts: list[PipelineExecutionContext], fallback: list[str]) -> list[str]:
    merged: list[str] = []
    for context in contexts:
        merged.extend(context.predictors)
    if merged:
        return _clean_str_list(merged)
    return _clean_str_list(fallback)


def _merge_feature_sets(
    contexts: list[PipelineExecutionContext],
    labels: list[str],
    merge_rule: str,
    min_votes: int,
) -> dict[str, object]:
    normalized_rule = str(merge_rule or "交集").strip()
    upstream_sets = [set(_clean_str_list(context.predictors)) for context in contexts]
    if not upstream_sets:
        return {
            "selected_predictors": [],
            "table_columns": ["predictor", "support_count", "support_ratio", "selected", "sources"],
            "table_rows": [],
            "effective_min_votes": min_votes,
            "upstream_count": 0,
        }

    all_predictors = sorted(set().union(*upstream_sets))
    upstream_count = len(upstream_sets)
    if normalized_rule == "交集":
        effective_min_votes = upstream_count
    elif normalized_rule == "并集":
        effective_min_votes = 1
    else:
        effective_min_votes = max(1, min(int(min_votes), upstream_count))

    selected_predictors: list[str] = []
    table_columns = ["predictor", "support_count", "support_ratio", "selected", "sources"]
    table_rows: list[list[object]] = []
    for predictor in all_predictors:
        support_indices = [index for index, predictor_set in enumerate(upstream_sets) if predictor in predictor_set]
        support_count = len(support_indices)
        selected = support_count >= effective_min_votes
        if selected:
            selected_predictors.append(predictor)
        sources = " | ".join(labels[index] for index in support_indices) if support_indices else ""
        table_rows.append(
            [
                predictor,
                support_count,
                round(support_count / upstream_count, 4) if upstream_count else 0,
                selected,
                sources,
            ]
        )

    return {
        "selected_predictors": _clean_str_list(selected_predictors),
        "table_columns": table_columns,
        "table_rows": table_rows,
        "effective_min_votes": effective_min_votes,
        "upstream_count": upstream_count,
    }


def _can_start_without_upstream(node: WorkflowNodeRequest) -> bool:
    if node.stage_id == "data-preparation":
        return True
    if node.stage_id == "model-development":
        data_source = str(node.values.get("dataSource") or "").strip()
        return data_source in {"原始数据", "原始", "原始数据源", "测试集", "测试", "训练集", "训练"}
    return False


def _plots_to_output_payload(plots) -> list[dict]:
    payloads: list[dict] = []
    for plot in plots or []:
        payloads.append(
            {
                "name": getattr(plot, "name", None),
                "filename": getattr(plot, "filename", None),
                "media_type": getattr(plot, "media_type", None),
                "content_base64": getattr(plot, "content_base64", None),
                "vector_pdf_filename": getattr(plot, "vector_pdf_filename", None),
                "vector_pdf_base64": getattr(plot, "vector_pdf_base64", None),
            }
        )
    return payloads


def _plots_to_artifacts(plots) -> list[dict]:
    artifacts: list[dict] = []
    for plot in plots or []:
        artifacts.append(
            {
                "artifact_type": "plot",
                "name": getattr(plot, "name", "plot"),
                "filename": getattr(plot, "filename", None),
                "media_type": getattr(plot, "media_type", None),
                "storage_key": None,
                "payload": {
                    "content_base64": getattr(plot, "content_base64", None),
                    "vector_pdf_filename": getattr(plot, "vector_pdf_filename", None),
                    "vector_pdf_base64": getattr(plot, "vector_pdf_base64", None),
                },
            }
        )
    return artifacts


def _artifact_from_bytes(
    *,
    artifact_type: str,
    name: str,
    filename: str,
    media_type: str,
    content: bytes,
) -> dict:
    return {
        "artifact_type": artifact_type,
        "name": name,
        "filename": filename,
        "media_type": media_type,
        "storage_key": None,
        "payload": {
            "content_base64": base64.b64encode(content).decode("ascii"),
        },
    }


def _table_csv_bytes(columns: list[str], rows: list[list[object]]) -> bytes:
    frame = pd.DataFrame(rows, columns=columns)
    return frame.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def _parse_int_value(raw_value: object, default: int, *, label: str) -> int:
    text = str(raw_value if raw_value is not None else default).strip() or str(default)
    try:
        return int(float(text))
    except ValueError as exc:
        raise BadRequest(f"{label}必须是有效整数") from exc


def _parse_float_value(raw_value: object, default: float, *, label: str) -> float:
    text = str(raw_value if raw_value is not None else default).strip() or str(default)
    try:
        return float(text)
    except ValueError as exc:
        raise BadRequest(f"{label}必须是有效数字") from exc


def _upstream_model_node(
    incoming_connections: list[SavedWorkflowConnection],
    nodes_by_id: dict[str, WorkflowNodeRequest],
) -> WorkflowNodeRequest | None:
    for connection in incoming_connections:
        source = nodes_by_id.get(connection.from_node_id)
        if source and source.stage_id == "model-development":
            return source
    return None


def _model_type_for_node(module_id: str) -> str:
    mapping = {
        "logistic-model": "logistic",
        "cox-model": "cox",
        "random-forest": "random-forest",
        "xgboost": "xgboost",
    }
    return mapping.get(module_id, module_id)


def _resolve_model_input_frames(
    *,
    node: WorkflowNodeRequest,
    context: PipelineExecutionContext,
    base_context: PipelineExecutionContext,
    has_upstream: bool,
) -> tuple[pd.DataFrame, pd.DataFrame | None, str]:
    """Pick train/test frames for model nodes based on node.values['dataSource'].

    Supported values (Chinese UI):
    - 上游输出: keep the current context df (default).
    - 原始数据: use the original dataset loaded at pipeline start.
    - 训练集: use current context df and keep split test set if available.
    - 测试集: use split test set (if available) as the input frame.
    """

    if has_upstream:
        return context.df, context.holdout_frames.get("测试集"), "上游输出"

    raw_value = str(node.values.get("dataSource") or "").strip()
    normalized = raw_value.replace("数据集", "").replace(" ", "")
    if normalized in {"原始", "原始数据", "原始数据源"}:
        return base_context.df.copy(), None, "原始数据"

    if normalized in {"测试", "测试集"}:
        test_df = context.holdout_frames.get("测试集")
        if test_df is not None and not test_df.empty:
            return test_df.copy(), None, "测试集"
        return context.df.copy(), None, "测试集"

    if normalized in {"训练", "训练集"}:
        return context.df, context.holdout_frames.get("测试集"), "训练集"

    # Default: upstream context.
    return context.df, context.holdout_frames.get("测试集"), "上游输出"


def _build_vif_design_matrix(
    df: pd.DataFrame,
    predictors: list[str],
    kind_overrides: dict[str, str] | None,
) -> tuple[pd.DataFrame, list[dict], list[str]]:
    kind_map = infer_dataframe_column_kinds(df, kind_overrides)
    design_parts: list[pd.DataFrame] = []
    groups: list[dict] = []
    logs: list[str] = []

    for predictor in predictors:
        if predictor not in df.columns:
            logs.append(f"{predictor} 不在当前数据中，已跳过 VIF 计算。")
            continue

        series = df[predictor]
        kind = kind_map.get(predictor, ("categorical", "auto"))[0]
        non_null = series.dropna()
        unique_count = int(non_null.nunique(dropna=True))
        if unique_count <= 1:
            logs.append(f"{predictor} 缺少有效变异，已跳过 VIF 计算。")
            continue

        if kind == "datetime":
            logs.append(f"{predictor} 为时间字段，当前不纳入 VIF 计算。")
            continue

        if kind == "numeric":
            numeric_series = pd.to_numeric(series, errors="coerce")
            if int(numeric_series.dropna().nunique(dropna=True)) <= 1:
                logs.append(f"{predictor} 转换为数值后无有效变异，已跳过 VIF 计算。")
                continue
            encoded_frame = pd.DataFrame({predictor: numeric_series.astype(float)})
            groups.append(
                {
                    "predictor": predictor,
                    "kind": "numeric",
                    "levels": unique_count,
                    "encoded_columns": [predictor],
                    "mapping_rows": [],
                }
            )
            design_parts.append(encoded_frame)
            continue

        if unique_count == 2:
            encoded_series, mapping_rows, action = _binary_encoding_payload(series)
            encoded_name = predictor
            encoded_frame = pd.DataFrame({encoded_name: pd.to_numeric(encoded_series, errors="coerce").astype(float)})
            groups.append(
                {
                    "predictor": predictor,
                    "kind": "binary",
                    "levels": unique_count,
                    "encoded_columns": [encoded_name],
                    "mapping_rows": [[predictor, raw_value, encoded_value, action] for raw_value, encoded_value in mapping_rows],
                }
            )
            design_parts.append(encoded_frame)
            continue

        encoded_frame = pd.get_dummies(
            series,
            prefix=predictor,
            prefix_sep="__",
            dummy_na=False,
            drop_first=True,
            dtype=int,
        ).astype(float)
        encoded_columns = encoded_frame.columns.tolist()
        if not encoded_columns:
            logs.append(f"{predictor} 在 VIF 编码后未生成有效列，已跳过。")
            continue
        groups.append(
            {
                "predictor": predictor,
                "kind": "multiclass",
                "levels": unique_count,
                "encoded_columns": encoded_columns,
                "mapping_rows": [],
            }
        )
        design_parts.append(encoded_frame)

    if not design_parts:
        return pd.DataFrame(), [], logs

    design_df = pd.concat(design_parts, axis=1)
    return design_df, groups, logs


def _compute_vif_values(design_df: pd.DataFrame) -> dict[str, float]:
    if design_df.empty:
        return {}

    numeric_df = design_df.apply(pd.to_numeric, errors="coerce").astype(float)
    numeric_df = numeric_df.loc[:, numeric_df.nunique(dropna=True) > 1]
    if numeric_df.empty:
        return {}

    complete_df = numeric_df.dropna(axis=0, how="any")
    if complete_df.empty:
        return {column: float("nan") for column in numeric_df.columns}

    values = complete_df.to_numpy(dtype=float)
    vif_map: dict[str, float] = {}

    for index, column in enumerate(complete_df.columns):
        y = values[:, index]
        other = np.delete(values, index, axis=1)
        if other.shape[1] == 0:
            vif_map[column] = 1.0
            continue

        design = np.column_stack([np.ones(other.shape[0]), other])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        predicted = design @ beta
        sse = float(np.square(y - predicted).sum())
        sst = float(np.square(y - y.mean()).sum())
        if sst <= 1e-12:
            vif_map[column] = float("nan")
            continue

        r_squared = 1.0 - (sse / sst)
        r_squared = min(max(r_squared, 0.0), 1.0)
        if 1.0 - r_squared <= 1e-12:
            vif_map[column] = float("inf")
            continue
        vif_map[column] = 1.0 / (1.0 - r_squared)

    return vif_map


def _run_vif_screen(
    *,
    df: pd.DataFrame,
    predictors: list[str],
    cutoff: float,
    strategy: str,
    kind_overrides: dict[str, str] | None,
) -> dict:
    active_predictors = _clean_str_list([predictor for predictor in predictors if predictor in df.columns])
    design_df, groups, prep_logs = _build_vif_design_matrix(df, active_predictors, kind_overrides)
    if design_df.empty or not groups:
        raise BadRequest("当前变量无法构造有效的 VIF 设计矩阵，请先完成编码或检查变量是否存在变异。")

    complete_cases = int(design_df.dropna(axis=0, how="any").shape[0])
    excluded_rows = int(design_df.shape[0] - complete_cases)
    logs = list(prep_logs)
    if excluded_rows > 0:
        logs.append(f"VIF 计算采用完整案例，因缺失排除 {excluded_rows} 行。")
    if complete_cases <= design_df.shape[1]:
        logs.append("完整案例数不大于编码后变量列数，VIF 结果可能不稳定。")

    summary_rows: list[dict] = []
    detail_rows: list[dict] = []
    removed_predictors: list[str] = []
    iteration_logs: list[str] = []

    working_predictors = list(active_predictors)
    iteration = 0
    latest_vif_map: dict[str, float] = {}
    latest_groups: list[dict] = []
    latest_design_df = design_df

    while working_predictors:
        iteration += 1
        latest_design_df, latest_groups, _ = _build_vif_design_matrix(df, working_predictors, kind_overrides)
        latest_vif_map = _compute_vif_values(latest_design_df)
        if not latest_groups:
            break

        current_summary_rows: list[dict] = []
        current_detail_rows: list[dict] = []
        candidate_scores: list[tuple[str, float]] = []

        for group in latest_groups:
            encoded_columns = group["encoded_columns"]
            column_vifs = [latest_vif_map.get(column) for column in encoded_columns]
            valid_vifs = [value for value in column_vifs if value is not None and not pd.isna(value)]
            max_vif = max(valid_vifs) if valid_vifs else float("nan")
            mean_vif = float(np.mean(valid_vifs)) if valid_vifs else float("nan")
            exceeds = bool(valid_vifs) and any(value > cutoff for value in valid_vifs)
            current_summary_rows.append(
                {
                    "predictor": group["predictor"],
                    "variable_kind": group["kind"],
                    "levels": group["levels"],
                    "encoded_columns": ", ".join(encoded_columns),
                    "encoded_column_count": len(encoded_columns),
                    "max_vif": max_vif,
                    "mean_vif": mean_vif,
                    "exceeds_cutoff": exceeds,
                    "decision": "移除" if exceeds and strategy == "删除高 VIF 变量" else "保留",
                }
            )
            for column in encoded_columns:
                current_detail_rows.append(
                    {
                        "predictor": group["predictor"],
                        "encoded_column": column,
                        "variable_kind": group["kind"],
                        "vif": latest_vif_map.get(column),
                        "exceeds_cutoff": (latest_vif_map.get(column) or 0) > cutoff if latest_vif_map.get(column) is not None and not pd.isna(latest_vif_map.get(column)) else False,
                    }
                )
            if exceeds:
                candidate_scores.append((group["predictor"], max_vif))

        summary_rows = current_summary_rows
        detail_rows = current_detail_rows

        if strategy != "删除高 VIF 变量" or not candidate_scores or len(working_predictors) <= 1:
            break

        candidate_scores.sort(key=lambda item: (float("-inf") if pd.isna(item[1]) else item[1], item[0]), reverse=True)
        removed_predictor = candidate_scores[0][0]
        removed_predictors.append(removed_predictor)
        working_predictors = [item for item in working_predictors if item != removed_predictor]
        iteration_logs.append(f"第 {iteration} 轮移除 {removed_predictor}，其最大 VIF 为 {candidate_scores[0][1]:.4f}。")

    retained_predictors = working_predictors or [item["predictor"] for item in latest_groups[:1]]
    if strategy == "删除高 VIF 变量" and removed_predictors:
        logs.extend(iteration_logs)
    if strategy == "人工确认后处理":
        logs.append("当前策略为人工确认，VIF 结果仅提示风险，不自动删除变量。")

    binary_mapping_rows: list[list[object]] = []
    for group in latest_groups:
        binary_mapping_rows.extend(group["mapping_rows"])

    return {
        "complete_cases": complete_cases,
        "excluded_rows": excluded_rows,
        "encoded_column_count": int(latest_design_df.shape[1]),
        "summary_rows": summary_rows,
        "detail_rows": detail_rows,
        "binary_mapping_rows": binary_mapping_rows,
        "retained_predictors": retained_predictors if strategy == "删除高 VIF 变量" else active_predictors,
        "removed_predictors": removed_predictors,
        "logs": logs,
    }


def _parse_ratio(ratio: str) -> list[int]:
    text = str(ratio or "").strip()
    parts = []
    for item in text.split(":"):
        item = item.strip()
        if not item:
            continue
        try:
            value = int(item)
        except ValueError as exc:
            raise BadRequest(f"不支持的划分比例: {ratio}") from exc
        if value <= 0:
            raise BadRequest(f"划分比例必须为正整数: {ratio}")
        parts.append(value)
    if len(parts) < 2:
        raise BadRequest("数据划分至少需要训练集和测试集两部分")
    return parts


def _split_indices_by_ratios(indices: np.ndarray, ratios: list[int]) -> list[np.ndarray]:
    if indices.size == 0:
        return [np.array([], dtype=int) for _ in ratios]
    boundaries = np.cumsum(ratios[:-1]) / sum(ratios)
    cut_points = [int(round(indices.size * boundary)) for boundary in boundaries]
    return [part.astype(int) for part in np.split(indices, cut_points)]


def _looks_like_identifier_column(column_name: str) -> bool:
    normalized = str(column_name or "").strip().lower()
    if not normalized:
        return False
    return (
        normalized in {"id", "patientid", "subjectid", "recordid", "caseid", "sampleid", "visitid", "encounterid"}
        or normalized.endswith("_id")
        or normalized.startswith("id_")
        or normalized.endswith("编号")
        or normalized.endswith("编码")
        or "流水号" in normalized
    )


def _is_split_baseline_candidate(
    df: pd.DataFrame,
    column_name: str,
    kind_map: dict[str, tuple[str, str]],
) -> bool:
    if column_name not in df.columns or column_name == "__split_group__":
        return False

    series = df[column_name]
    non_null = series.dropna()
    non_null_count = int(non_null.shape[0])
    if non_null_count == 0:
        return False

    kind = kind_map.get(column_name, ("categorical", "auto"))[0]
    if kind == "datetime":
        return False

    if _looks_like_identifier_column(column_name):
        return False

    unique_count = int(non_null.nunique(dropna=True))
    if unique_count <= 1:
        return False

    if kind in {"categorical", "boolean"}:
        if unique_count > 20 or (non_null_count >= 10 and unique_count / max(non_null_count, 1) >= 0.5):
            return False

    return True


def _select_split_baseline_variables(
    df: pd.DataFrame,
    *,
    predictor_variables: list[str],
    outcome_variable: str | None,
    time_variable: str | None,
    event_variable: str | None,
    split_field_used: str | None,
    kind_overrides: dict[str, str] | None,
) -> list[str]:
    kind_map = infer_dataframe_column_kinds(df, kind_overrides)

    def _eligible(columns: list[str]) -> list[str]:
        return [
            column
            for column in _clean_str_list(columns)
            if _is_split_baseline_candidate(df, column, kind_map)
        ]

    predictor_candidates = _eligible([item for item in predictor_variables if item in df.columns])
    priority_candidates = _eligible([
        outcome_variable or "",
        time_variable or "",
        event_variable or "",
        split_field_used or "",
    ])
    fallback_candidates = _eligible(df.columns.tolist())

    if predictor_candidates:
        return _clean_str_list([*predictor_candidates, *priority_candidates])

    return _clean_str_list([*priority_candidates, *fallback_candidates])


def _execute_split(
    df: pd.DataFrame,
    *,
    template_kind: Literal["binary", "survival"],
    outcome_variable: str | None,
    time_variable: str | None,
    event_variable: str | None,
    predictor_variables: list[str],
    ratio: str,
    sampling: str,
    stratify_field: str | None,
    time_split_field: str | None,
    seed: int,
    dataset_name: str,
    kind_overrides: dict[str, str] | None,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict, list[dict], list[dict], list[dict], list[str]]:
    ratios = _parse_ratio(ratio)
    rng = np.random.default_rng(seed)
    split_labels = ["训练集", "测试集", "验证集"][: len(ratios)]
    if len(split_labels) < len(ratios):
        split_labels.extend([f"子集{i + 1}" for i in range(len(split_labels), len(ratios))])

    index_parts: list[np.ndarray]
    split_field_used: str | None = None
    fallback_used = False
    if sampling == "分层抽样":
        fallback_column = outcome_variable if template_kind == "binary" else event_variable
        stratify_column = str(stratify_field or "").strip() or fallback_column
        fallback_used = not str(stratify_field or "").strip() and bool(stratify_column)
        if not stratify_column or stratify_column not in df.columns:
            raise BadRequest("当前分层抽样需要有效的分层变量")
        split_field_used = stratify_column
        parts_buffer = [list() for _ in ratios]
        stratify_series = df[stratify_column].fillna("__missing__").astype(str)
        for _, group_indices in stratify_series.groupby(stratify_series).groups.items():
            group_array = np.array(list(group_indices), dtype=int)
            rng.shuffle(group_array)
            group_parts = _split_indices_by_ratios(group_array, ratios)
            for idx, values in enumerate(group_parts):
                if values.size:
                    parts_buffer[idx].extend(values.tolist())
        index_parts = [np.array(sorted(values), dtype=int) for values in parts_buffer]
    elif sampling == "时间切分":
        fallback_column = time_variable if time_variable and time_variable in df.columns else "follow_up_days" if "follow_up_days" in df.columns else None
        sort_column = str(time_split_field or "").strip() or fallback_column
        fallback_used = not str(time_split_field or "").strip() and bool(sort_column)
        if not sort_column or sort_column not in df.columns:
            raise BadRequest("当前时间切分需要有效的时间切分字段")
        split_field_used = sort_column
        ordered_indices = (
            df.sort_values(by=sort_column, kind="stable").index.to_numpy(dtype=int)
            if sort_column
            else df.index.to_numpy(dtype=int)
        )
        index_parts = _split_indices_by_ratios(ordered_indices, ratios)
    else:
        shuffled_indices = df.index.to_numpy(dtype=int).copy()
        rng.shuffle(shuffled_indices)
        index_parts = _split_indices_by_ratios(shuffled_indices, ratios)

    split_frames = {
        split_labels[idx]: df.loc[index_part].copy().reset_index(drop=True)
        for idx, index_part in enumerate(index_parts)
    }
    train_df = split_frames[split_labels[0]]
    if train_df.empty:
        raise BadRequest("划分后训练集为空，请调整比例或抽样方式")

    comparison_variables = _select_split_baseline_variables(
        df,
        predictor_variables=predictor_variables,
        outcome_variable=outcome_variable,
        time_variable=time_variable,
        event_variable=event_variable,
        split_field_used=split_field_used,
        kind_overrides=kind_overrides,
    )
    output_tables: list[dict] = []
    artifacts: list[dict] = []
    logs = [f"{label}: {len(frame)} 行" for label, frame in split_frames.items()]
    if split_field_used:
        logs.append(f"{sampling}使用字段：{split_field_used}")
    if fallback_used and split_field_used:
        logs.append(f"未显式配置切分字段，已兼容回退到 {split_field_used}。")

    output_tables.append(
        {
            "name": "split_summary",
            "columns": ["subset", "rows", "ratio"],
            "rows": [
                [label, int(frame.shape[0]), f"{ratios[idx]}/{sum(ratios)}"]
                for idx, (label, frame) in enumerate(split_frames.items())
            ],
        }
    )

    if sampling == "分层抽样" and split_field_used:
        stratify_table_rows: list[list[object]] = []
        category_counts = df[split_field_used].fillna("__missing__").astype(str).value_counts()
        category_order = category_counts.index.tolist()
        small_categories = [str(category) for category, count in category_counts.items() if int(count) < len(ratios)]
        if small_categories:
            logs.append(f"分层变量中存在样本量较小的类别：{', '.join(small_categories[:5])}。部分子集可能不包含这些类别。")
        for category in category_order:
            for label, frame in split_frames.items():
                category_count = int(frame[split_field_used].fillna("__missing__").astype(str).eq(category).sum())
                stratify_table_rows.append([category, label, category_count])
        output_tables.append(
            {
                "name": "split_stratified_distribution",
                "columns": ["stratify_value", "subset", "rows"],
                "rows": stratify_table_rows,
            }
        )

    for label, frame in split_frames.items():
        content = frame.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        artifacts.append(
            _artifact_from_bytes(
                artifact_type="dataset",
                name=f"{label}数据集",
                filename=f"{dataset_name}_{label}.csv",
                media_type="text/csv",
                content=content,
            )
        )

    if comparison_variables:
        baseline_df = pd.concat(
            [frame.assign(__split_group__=label) for label, frame in split_frames.items()],
            ignore_index=True,
        )
        try:
            baseline_result = generate_tableone(
                content=dataframe_to_csv_bytes(baseline_df),
                ext=".csv",
                dataset_name=f"{dataset_name}_split_baseline",
                group_variable="__split_group__",
                variables=comparison_variables,
                decimals=1,
                type_overrides={**(kind_overrides or {}), "__split_group__": "categorical"},
            )
            output_tables.append(
                {
                    "name": "split_baseline",
                    "columns": baseline_result.headers,
                    "rows": baseline_result.rows,
                }
            )
            artifacts.append(
                _artifact_from_bytes(
                    artifact_type="table",
                    name="数据切分基线比较",
                    filename=f"{dataset_name}_split_baseline.xlsx",
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    content=baseline_result.excel_content,
                )
            )
            logs.append(f"已生成数据切分基线比较表，共纳入 {len(comparison_variables)} 个变量。")
        except BadRequest as exc:
            logs.append(f"数据切分基线比较未生成：{exc.detail}")
    else:
        logs.append("数据切分基线比较未生成：当前未筛选出可用于基线统计的变量。")

    output_summary = {
        "sampling": sampling,
        "ratio": ratio,
        "seed": seed,
        "split_field": split_field_used,
        "fallback_used": fallback_used,
        "splits": {label: int(frame.shape[0]) for label, frame in split_frames.items()},
        "downstream_dataset": split_labels[0],
    }
    return train_df, split_frames, output_summary, output_tables, [], artifacts, logs


def _univariate_threshold_from_rule(rule: str) -> float | None:
    normalized = str(rule or "").strip().lower()
    if normalized in {"p < 0.05", "p<0.05"}:
        return 0.05
    if normalized in {"p < 0.10", "p<0.10"}:
        return 0.10
    if normalized in {"仅展示不筛除", "display_only"}:
        return None
    return 0.10


def run_clinical_prediction_pipeline(
    *,
    content: bytes,
    ext: str,
    dataset_name: str,
    template_kind: Literal["binary", "survival"],
    outcome_variable: str | None,
    time_variable: str | None,
    event_variable: str | None,
    predictor_variables: list[str],
    alpha: float,
    nfolds: int,
    workflow_nodes: list[WorkflowNodeRequest],
    workflow_connections: list[SavedWorkflowConnection],
    predictor_kind_overrides: dict[str, str] | None = None,
    skip_completed: bool = False,
    dataset_id: str | None = None,
    workflow_id: str | None = None,
) -> ClinicalPipelineExecutionResult:
    df = load_tabular_dataframe(content, ext)
    base_kind_overrides = dict(predictor_kind_overrides or {})
    original_rows = int(df.shape[0])
    original_columns = int(df.shape[1])
    analysis_columns = _required_columns(
        df=df,
        workflow_nodes=workflow_nodes,
        template_kind=template_kind,
        outcome_variable=outcome_variable,
        time_variable=time_variable,
        event_variable=event_variable,
        predictor_variables=predictor_variables,
    )
    _validate_columns(df, analysis_columns)
    incoming_map = _incoming_connection_map(workflow_nodes, workflow_connections)
    requires_binary_outcome_modules = {"univariate-screen", "lasso-selection", "rf-importance", "boruta-selection", "logistic-model", "roc", "calibration", "dca", "nomogram"}
    runnable_requires_binary = [
        node
        for node in workflow_nodes
        if node.module_id in requires_binary_outcome_modules
        and (bool(incoming_map.get(node.id)) or _can_start_without_upstream(node))
    ]
    if template_kind == "binary" and outcome_variable and runnable_requires_binary:
        if outcome_variable not in df.columns:
            raise BadRequest(f"数据集中缺少以下变量: {outcome_variable}")
        if not _supports_binary_outcome(df[outcome_variable]):
            raise BadRequest(
                f"当前流程包含特征筛选或 Logistic 相关节点，但结局变量 {outcome_variable} 不是二分类。请更换为二分类结局，或移除这些节点后再运行。"
            )

    nodes_by_module = _node_map(workflow_nodes)
    nodes_by_id = _node_id_map(workflow_nodes)
    ordered_nodes = _topological_nodes(workflow_nodes, workflow_connections)
    logs: list[str] = [
        f"已加载数据集 {dataset_name}，原始维度 {original_rows} 行 × {original_columns} 列。",
        f"当前模板为{'二分类临床预测模型' if template_kind == 'binary' else '生存预测模型'}。",
        f"本次将按节点连线拓扑执行，共识别 {len(ordered_nodes)} 个节点、{len(workflow_connections)} 条连线。",
    ]
    node_results: list[PipelineNodeStatusData] = []
    engine_notes: list[str] = []
    cleaning_operations: list[str] = []
    node_contexts: dict[str, PipelineExecutionContext] = {}
    lasso_result: LassoRegressionExecutionResult | None = None
    logistic_result: LogisticRegressionExecutionResult | None = None
    cox_result: CoxRegressionExecutionResult | None = None
    random_forest_model_result: TreeModelExecutionResult | None = None
    xgboost_model_result: TreeModelExecutionResult | None = None
    final_predictors = _clean_str_list(predictor_variables)
    base_context = PipelineExecutionContext(
        df=df.copy(),
        predictors=final_predictors,
        kind_overrides=dict(base_kind_overrides),
    )

    # --- Incremental execution: load previous run cache ---
    cache_key = f"{dataset_id or ''}:{workflow_id or ''}"
    prev_cache = _pipeline_run_cache.get(cache_key, {}) if skip_completed else {}
    # Build per-node config hashes to detect changes
    node_hashes: dict[str, str] = {node.id: _node_config_hash(node) for node in ordered_nodes}
    # Track which nodes are invalidated (config changed or upstream invalidated)
    invalidated_node_ids: set[str] = set()
    skipped_count = 0

    for node in ordered_nodes:
        # --- Incremental execution: try to reuse cached results ---
        upstream_ids = {c.from_node_id for c in incoming_map.get(node.id, [])}
        upstream_invalidated = bool(upstream_ids & invalidated_node_ids)
        cached_entry = prev_cache.get(node.id)
        if (
            cached_entry
            and not upstream_invalidated
            and cached_entry[0] == node_hashes.get(node.id)
        ):
            # Cache hit: reuse previous context and result
            _, cached_ctx, cached_result = cached_entry
            node_contexts[node.id] = cached_ctx
            node_results.append(cached_result)
            # Propagate model results from cached context
            if cached_ctx.lasso_result:
                lasso_result = cached_ctx.lasso_result
            if cached_ctx.logistic_result:
                logistic_result = cached_ctx.logistic_result
            if cached_ctx.cox_result:
                cox_result = cached_ctx.cox_result
            if cached_ctx.random_forest_model_result:
                random_forest_model_result = cached_ctx.random_forest_model_result
            if cached_ctx.xgboost_model_result:
                xgboost_model_result = cached_ctx.xgboost_model_result
            skipped_count += 1
            continue
        # Node not cached or invalidated — mark it and all downstream as invalidated
        invalidated_node_ids.add(node.id)

        incoming_connections = incoming_map.get(node.id, [])
        upstream_contexts = [
            node_contexts[connection.from_node_id]
            for connection in incoming_connections
            if connection.from_node_id in node_contexts
        ]

        # Determine the base DataFrame: if the connection comes from a split
        # node's "test" output port, use the test set from holdout_frames.
        base_df = base_context.df.copy()
        if upstream_contexts:
            first_connection = incoming_connections[0] if incoming_connections else None
            first_upstream = upstream_contexts[0]
            if (
                first_connection
                and getattr(first_connection, "output_port_id", None) == "test"
                and first_upstream.holdout_frames
            ):
                test_df = first_upstream.holdout_frames.get("测试集")
                base_df = test_df.copy() if test_df is not None else first_upstream.df.copy()
            else:
                base_df = first_upstream.df.copy()

        base_predictors = _merge_predictors(upstream_contexts, final_predictors)
        context = PipelineExecutionContext(
            df=base_df,
            predictors=base_predictors,
            kind_overrides=dict(upstream_contexts[-1].kind_overrides) if upstream_contexts else dict(base_kind_overrides),
            holdout_frames=upstream_contexts[-1].holdout_frames if upstream_contexts else {},
            lasso_result=upstream_contexts[-1].lasso_result if upstream_contexts else None,
            logistic_result=upstream_contexts[-1].logistic_result if upstream_contexts else None,
            cox_result=upstream_contexts[-1].cox_result if upstream_contexts else None,
            random_forest_model_result=upstream_contexts[-1].random_forest_model_result if upstream_contexts else None,
            xgboost_model_result=upstream_contexts[-1].xgboost_model_result if upstream_contexts else None,
            univariate_result=upstream_contexts[-1].univariate_result if upstream_contexts else None,
        )

        if incoming_connections and not upstream_contexts:
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="skipped",
                    message="上游节点尚未产生可用结果，本节点未执行",
                    details=["请检查上游节点是否执行成功，或是否被错误跳过。"],
                )
            )
            continue

        if not incoming_connections and not _can_start_without_upstream(node):
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="skipped",
                    message="该节点未接入上游，当前拓扑不会执行它",
                    details=["请把该节点连接到上游数据准备或模型节点后再运行。"],
                )
            )
            continue

        if node.module_id == "field-mapping":
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message="字段映射已用于本次运行参数校验",
                    details=[f"分析变量: {', '.join(analysis_columns[:6])}"],
                    input_snapshot={
                        "outcome_variable": outcome_variable,
                        "time_variable": time_variable,
                        "event_variable": event_variable,
                        "predictor_variables": predictor_variables,
                        "node_values": node.values,
                    },
                    output_summary={
                        "mapped_fields": {
                            "id": node.values.get("idField"),
                            "outcome": node.values.get("outcomeField") or outcome_variable,
                            "time": node.values.get("timeField") or time_variable,
                        },
                        "predictor_count": len(predictor_variables),
                    },
                    output_tables=[
                        {
                            "name": "field_mapping",
                            "columns": ["role", "field"],
                            "rows": [
                                ["id", node.values.get("idField") or ""],
                                ["outcome", node.values.get("outcomeField") or outcome_variable or ""],
                                ["time", node.values.get("timeField") or time_variable or ""],
                                ["event", event_variable or ""],
                            ],
                        }
                    ],
                    next_variable_set=_clean_str_list(predictor_variables),
                )
            )
        elif node.module_id == "missing-value":
            context.df, operations, context.predictors, node_result = _apply_missing_value_node(
                context.df,
                dataset_name=dataset_name,
                analysis_columns=analysis_columns,
                node=node,
                outcome_variable=outcome_variable,
                time_variable=time_variable,
                event_variable=event_variable,
                predictors=context.predictors,
            )
            cleaning_operations.extend([item for item in operations if item not in cleaning_operations])
            if node_result:
                effective_analysis_columns = _clean_str_list(
                    [
                        *[column for column in analysis_columns if column in context.df.columns],
                        *context.predictors,
                        *[item for item in [outcome_variable, time_variable, event_variable] if item and item in context.df.columns],
                    ]
                ) or list(context.df.columns)
                node_result.input_snapshot = {
                    "method": node.values.get("method") or "多重插补",
                    "threshold": node.values.get("threshold") or "0.20",
                    "input_rows": int(base_df.shape[0]),
                    "analysis_columns": effective_analysis_columns,
                }
                node_result.output_summary = {
                    "output_rows": int(context.df.shape[0]),
                    "removed_rows": int(base_df.shape[0]) - int(context.df.shape[0]),
                    "predictor_count": len(context.predictors),
                    "operation_count": len(operations),
                }
                node_results.append(node_result)
                logs.extend(node_result.details)
        elif node.module_id == "split":
            seed_value = int(str(node.values.get("seed") or "2026").strip() or "2026")
            stratify_field = str(node.values.get("stratifyField") or "").strip() or None
            time_split_field = str(node.values.get("timeSplitField") or "").strip() or None
            train_df, split_frames, split_summary, split_tables, split_plots, split_artifacts, split_logs = _execute_split(
                context.df,
                template_kind=template_kind,
                outcome_variable=outcome_variable,
                time_variable=time_variable,
                event_variable=event_variable,
                predictor_variables=context.predictors,
                ratio=node.values.get("ratio") or "7:3",
                sampling=node.values.get("sampling") or "分层抽样",
                stratify_field=stratify_field,
                time_split_field=time_split_field,
                seed=seed_value,
                dataset_name=dataset_name,
                kind_overrides=context.kind_overrides,
            )
            context.df = train_df
            context.holdout_frames = split_frames
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message="训练/测试集已真实划分，下游模型将默认使用训练集继续执行",
                    details=[
                        f"划分比例: {node.values.get('ratio') or '7:3'}",
                        f"划分方式: {node.values.get('sampling') or '分层抽样'}",
                        f"切分字段: {split_summary.get('split_field') or '随机划分无需指定'}",
                        f"随机种子: {seed_value}",
                    ],
                    input_snapshot={
                        "input_rows": int(base_df.shape[0]),
                        "predictors": context.predictors,
                        "node_values": node.values,
                    },
                    output_summary=split_summary,
                    output_tables=split_tables,
                    output_plots=split_plots,
                    artifacts=split_artifacts,
                    logs=split_logs,
                    next_dataset_ref=f"inmemory://{node.id}/训练集",
                    next_variable_set=context.predictors,
                )
            )
            engine_notes.append("split 节点已真实执行；当前下游模型默认继续使用训练集，测试/验证集结果将在后续评估节点接入。")
        elif node.module_id == "encoding":
            context.df, context.predictors, context.kind_overrides, context.holdout_frames, node_result = _apply_encoding_node(
                context.df,
                dataset_name=dataset_name,
                node=node,
                predictors=context.predictors,
                template_kind=template_kind,
                outcome_variable=outcome_variable,
                event_variable=event_variable,
                kind_overrides=context.kind_overrides,
                holdout_frames=context.holdout_frames,
            )
            final_predictors = context.predictors
            if node_result:
                cleaning_operations.extend([item for item in node_result.details if item not in cleaning_operations])
                node_results.append(node_result)
                logs.extend(node_result.details)
        elif node.module_id == "univariate-screen":
            threshold_rule = node.values.get("rule") or "P < 0.10"
            threshold_value = _univariate_threshold_from_rule(threshold_rule)
            keep_clinical = (node.values.get("keepClinical") or "是") == "是"
            if template_kind == "binary":
                screen_result = run_univariate_logistic_screen(
                    df=context.df,
                    dataset_name=dataset_name,
                    outcome_variable=outcome_variable or "",
                    predictor_variables=context.predictors,
                    threshold=threshold_value,
                    predictor_kind_overrides=context.kind_overrides,
                )
            else:
                screen_result = run_univariate_cox_screen(
                    df=context.df,
                    dataset_name=dataset_name,
                    time_variable=time_variable or "",
                    event_variable=event_variable or "",
                    predictor_variables=context.predictors,
                    threshold=threshold_value,
                    predictor_kind_overrides=context.kind_overrides,
                )
            context.univariate_result = screen_result
            selected_predictors = screen_result.selected_predictors
            if not selected_predictors and keep_clinical:
                selected_predictors = context.predictors
            context.predictors = selected_predictors
            final_predictors = context.predictors
            effect_label = screen_result.effect_label
            table_columns = ["predictor", "term", "coefficient", "std_error", effect_label, "conf_low", "conf_high", "p_value", "selected"]
            table_rows = [
                [
                    item.predictor,
                    item.term,
                    item.coefficient,
                    item.std_error,
                    item.effect_value,
                    item.conf_low,
                    item.conf_high,
                    item.p_value,
                    item.selected,
                ]
                for item in screen_result.coefficients
            ]
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message=f"单因素筛选已完成，当前进入下游分析的变量数为 {len(context.predictors)}",
                    details=[
                        f"筛选规则: {threshold_rule}",
                        f"保留临床变量: {'是' if keep_clinical else '否'}",
                        screen_result.note,
                    ],
                    input_snapshot={
                        "input_rows": int(context.df.shape[0]),
                        "predictors": base_predictors,
                        "rule": threshold_rule,
                        "keep_clinical": keep_clinical,
                    },
                    output_summary={
                        "analysis_kind": screen_result.analysis_kind,
                        "sample_size": screen_result.sample_size,
                        "excluded_rows": screen_result.excluded_rows,
                        "selected_predictor_count": len(context.predictors),
                        "effect_label": effect_label,
                    },
                    output_tables=[
                        {
                            "name": f"{screen_result.analysis_kind}_univariate_screen",
                            "columns": table_columns,
                            "rows": table_rows,
                        }
                    ],
                    artifacts=[
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="单因素筛选结果",
                            filename=f"{dataset_name}_{screen_result.analysis_kind}_univariate_screen.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(table_columns, table_rows),
                        )
                    ],
                    logs=[
                        screen_result.note,
                        f"selected_predictors={', '.join(context.predictors) if context.predictors else 'none'}",
                    ],
                    next_variable_set=context.predictors,
                )
            )
        elif node.module_id == "vif":
            if not context.predictors:
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="skipped",
                        message="上游筛选后已无剩余预测变量，VIF 未执行",
                        details=["请放宽上游筛选阈值，或在字段映射中重新选择候选变量。"],
                    )
                )
                node_contexts[node.id] = context
                continue
            cutoff_raw = str(node.values.get("cutoff") or "5").strip() or "5"
            try:
                cutoff = float(cutoff_raw)
            except ValueError as exc:
                raise BadRequest("VIF 阈值必须是有效数字") from exc
            strategy = "删除高 VIF 变量"
            vif_result = _run_vif_screen(
                df=context.df,
                predictors=context.predictors,
                cutoff=cutoff,
                strategy=strategy,
                kind_overrides=context.kind_overrides,
            )
            context.predictors = _clean_str_list(vif_result["retained_predictors"])
            final_predictors = context.predictors
            summary_columns = ["predictor", "variable_kind", "levels", "encoded_columns", "encoded_column_count", "max_vif", "mean_vif", "exceeds_cutoff", "decision"]
            summary_rows = [
                [
                    item["predictor"],
                    item["variable_kind"],
                    item["levels"],
                    item["encoded_columns"],
                    item["encoded_column_count"],
                    item["max_vif"],
                    item["mean_vif"],
                    item["exceeds_cutoff"],
                    item["decision"],
                ]
                for item in vif_result["summary_rows"]
            ]
            detail_columns = ["predictor", "encoded_column", "variable_kind", "vif", "exceeds_cutoff"]
            detail_rows = [
                [
                    item["predictor"],
                    item["encoded_column"],
                    item["variable_kind"],
                    item["vif"],
                    item["exceeds_cutoff"],
                ]
                for item in vif_result["detail_rows"]
            ]
            output_tables = [
                {
                    "name": "vif_summary",
                    "columns": summary_columns,
                    "rows": summary_rows,
                },
                {
                    "name": "vif_detail",
                    "columns": detail_columns,
                    "rows": detail_rows,
                },
            ]
            if vif_result["binary_mapping_rows"]:
                output_tables.append(
                    {
                        "name": "vif_binary_mapping",
                        "columns": ["predictor", "raw_value", "encoded_value", "action"],
                        "rows": vif_result["binary_mapping_rows"],
                    }
                )
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message=(
                        f"VIF 共线性检查已完成，当前保留 {len(context.predictors)} 个变量"
                        if strategy == "删除高 VIF 变量"
                        else "VIF 共线性检查已完成，结果已生成供人工确认"
                    ),
                    details=[
                        f"VIF 阈值: {cutoff}",
                        "处理策略: 超阈值自动剔除",
                        f"完整案例数: {vif_result['complete_cases']}",
                        f"移除变量数: {len(vif_result['removed_predictors'])}",
                    ],
                    input_snapshot={
                        "input_rows": int(context.df.shape[0]),
                        "predictors": base_predictors,
                        "cutoff": cutoff,
                        "strategy": "删除高 VIF 变量",
                    },
                    output_summary={
                        "complete_cases": vif_result["complete_cases"],
                        "excluded_rows": vif_result["excluded_rows"],
                        "encoded_column_count": vif_result["encoded_column_count"],
                        "retained_predictor_count": len(context.predictors),
                        "removed_predictor_count": len(vif_result["removed_predictors"]),
                    },
                    output_tables=output_tables,
                    artifacts=[
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="VIF 汇总结果",
                            filename=f"{dataset_name}_vif_summary.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(summary_columns, summary_rows),
                        ),
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="VIF 明细结果",
                            filename=f"{dataset_name}_vif_detail.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(detail_columns, detail_rows),
                        ),
                    ],
                    logs=vif_result["logs"],
                    next_variable_set=context.predictors,
                )
            )
            logs.extend(vif_result["logs"])
        elif node.module_id == "lasso-selection":
            if not context.predictors:
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="skipped",
                        message="上游筛选后已无剩余预测变量，LASSO 未执行",
                        details=["请放宽单因素或 VIF 的筛选条件后重试。"],
                    )
                )
                node_contexts[node.id] = context
                continue
            if template_kind == "survival":
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="unsupported",
                        message="当前仓库尚未接入 LASSO-Cox 特征选择引擎",
                    )
                )
            else:
                lasso_result = run_lasso_regression(
                    df=context.df,
                    dataset_name=dataset_name,
                    outcome_variable=outcome_variable or "",
                    predictor_variables=context.predictors,
                    alpha=alpha,
                    nfolds=nfolds,
                    predictor_kind_overrides=context.kind_overrides,
                )
                criterion = node.values.get("criterion") or "lambda.1se"
                selected = _extract_lasso_predictors(lasso_result, criterion)
                context.lasso_result = lasso_result
                context.predictors = selected or context.predictors
                final_predictors = context.predictors
                table_columns = ["term", "coef_lambda_min", "coef_lambda_1se", "selected_lambda_min", "selected_lambda_1se"]
                table_rows = [
                    [
                        item.term,
                        item.coefficient_lambda_min,
                        item.coefficient_lambda_1se,
                        item.selected_at_lambda_min,
                        item.selected_at_lambda_1se,
                    ]
                    for item in lasso_result.selected_features
                ]
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="completed",
                        message=f"LASSO 已完成并筛选出 {len(context.predictors)} 个候选变量",
                        details=[
                            f"规则: {criterion}",
                            f"候选变量: {', '.join(context.predictors[:10]) or '未筛出变量，已回退上游变量'}",
                        ],
                        input_snapshot={
                            "input_rows": int(context.df.shape[0]),
                            "predictor_count": len(base_predictors),
                            "criterion": criterion,
                        },
                        output_summary={
                            "selected_predictor_count": len(context.predictors),
                            "lambda_min": lasso_result.lambda_min,
                            "lambda_1se": lasso_result.lambda_1se,
                        },
                        output_tables=[
                            {
                                "name": "lasso_selected_features",
                                "columns": table_columns,
                                "rows": table_rows,
                            }
                        ],
                        output_plots=_plots_to_output_payload(lasso_result.plots),
                        artifacts=[
                            _artifact_from_bytes(
                                artifact_type="table",
                                name="LASSO 回归三线表",
                                filename=f"{dataset_name}_lasso_selected_features.csv",
                                media_type="text/csv",
                                content=_table_csv_bytes(table_columns, table_rows),
                            )
                        ],
                        logs=[f"LASSO criterion={criterion}", f"selected={len(context.predictors)}"],
                        next_variable_set=context.predictors,
                    )
                )
                logs.append(f"LASSO 节点 {node.label} 已执行，当前候选变量数 {len(context.predictors)}。")
        elif node.module_id == "rf-importance":
            if not context.predictors:
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="skipped",
                        message="上游筛选后已无剩余预测变量，随机森林变量重要度未执行",
                        details=["请放宽上游筛选阈值，或在字段映射中重新选择候选变量。"],
                    )
                )
                node_contexts[node.id] = context
                continue
            if template_kind == "survival":
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="unsupported",
                        message="当前仓库尚未接入生存结局的随机森林变量重要度筛选引擎",
                    )
                )
            else:
                trees_raw = str(node.values.get("trees") or "500").strip() or "500"
                top_n_raw = str(node.values.get("topN") or "10").strip() or "10"
                try:
                    trees = int(trees_raw)
                    top_n = int(top_n_raw)
                except ValueError as exc:
                    raise BadRequest("随机森林参数必须是有效整数") from exc
                rf_result = run_random_forest_importance_selection(
                    df=context.df,
                    dataset_name=dataset_name,
                    outcome_variable=outcome_variable or "",
                    predictor_variables=context.predictors,
                    trees=trees,
                    top_n=top_n,
                    predictor_kind_overrides=context.kind_overrides,
                )
                selected_predictors = _clean_str_list(rf_result.selected_predictors)
                fallback_used = not selected_predictors
                context.predictors = selected_predictors or context.predictors
                final_predictors = context.predictors
                table_columns = ["predictor", "importance", "secondary_importance", "normalized_importance", "rank", "selected"]
                table_rows = [
                    [
                        item.predictor,
                        item.importance,
                        item.secondary_importance,
                        item.normalized_importance,
                        item.rank,
                        item.selected,
                    ]
                    for item in rf_result.importance_rows
                ]
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="completed",
                        message=f"随机森林变量重要度筛选已完成，当前保留 {len(context.predictors)} 个变量",
                        details=[
                            f"树数量: {rf_result.trees}",
                            f"保留前 N 个变量: {rf_result.top_n}",
                            f"重要度指标: {rf_result.importance_metric}",
                            "未筛出变量，已回退上游变量。" if fallback_used else f"候选变量: {', '.join(context.predictors[:10])}",
                        ],
                        input_snapshot={
                            "input_rows": int(context.df.shape[0]),
                            "predictor_count": len(base_predictors),
                            "trees": rf_result.trees,
                            "top_n": rf_result.top_n,
                        },
                        output_summary={
                            "sample_size": rf_result.sample_size,
                            "excluded_rows": rf_result.excluded_rows,
                            "selected_predictor_count": len(context.predictors),
                            "importance_metric": rf_result.importance_metric,
                        },
                        output_tables=[
                            {
                                "name": "rf_importance",
                                "columns": table_columns,
                                "rows": table_rows,
                            }
                        ],
                        output_plots=_plots_to_output_payload(rf_result.plots),
                        artifacts=[
                            _artifact_from_bytes(
                                artifact_type="table",
                                name="随机森林变量重要度结果",
                                filename=f"{dataset_name}_rf_importance.csv",
                                media_type="text/csv",
                                content=_table_csv_bytes(table_columns, table_rows),
                            ),
                        ],
                        logs=[
                            rf_result.note,
                            f"selected_predictors={', '.join(context.predictors) if context.predictors else 'none'}",
                        ],
                        next_variable_set=context.predictors,
                    )
                )
                logs.append(f"随机森林变量重要度节点 {node.label} 已执行，当前候选变量数 {len(context.predictors)}。")
        elif node.module_id == "boruta-selection":
            if not context.predictors:
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="skipped",
                        message="上游筛选后已无剩余预测变量，Boruta 未执行",
                        details=["请放宽上游筛选阈值，或在字段映射中重新选择候选变量。"],
                    )
                )
                node_contexts[node.id] = context
                continue
            if template_kind == "survival":
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="unsupported",
                        message="当前仓库尚未接入生存结局的 Boruta 变量筛选引擎",
                    )
                )
            else:
                max_runs_raw = str(node.values.get("maxRuns") or "100").strip() or "100"
                try:
                    max_runs = int(max_runs_raw)
                except ValueError as exc:
                    raise BadRequest("Boruta 最大迭代次数必须是有效整数") from exc
                boruta_result = run_boruta_selection(
                    df=context.df,
                    dataset_name=dataset_name,
                    outcome_variable=outcome_variable or "",
                    predictor_variables=context.predictors,
                    max_runs=max_runs,
                    predictor_kind_overrides=context.kind_overrides,
                )
                selected_predictors = _clean_str_list(boruta_result.selected_predictors)
                fallback_used = not selected_predictors
                context.predictors = selected_predictors or context.predictors
                final_predictors = context.predictors
                table_columns = ["predictor", "decision", "mean_importance", "median_importance", "min_importance", "max_importance", "normalized_hits", "selected"]
                table_rows = [
                    [
                        item.predictor,
                        item.decision,
                        item.mean_importance,
                        item.median_importance,
                        item.min_importance,
                        item.max_importance,
                        item.normalized_hits,
                        item.selected,
                    ]
                    for item in boruta_result.features
                ]
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="completed",
                        message=f"Boruta 变量筛选已完成，当前保留 {len(context.predictors)} 个变量",
                        details=[
                            f"最大迭代次数: {boruta_result.max_runs}",
                            f"实际运行次数: {boruta_result.actual_runs}",
                            f"Confirmed: {boruta_result.confirmed_count}",
                            f"Rejected: {boruta_result.rejected_count}",
                            "未确认变量，已回退上游变量。" if fallback_used else f"候选变量: {', '.join(context.predictors[:10])}",
                        ],
                        input_snapshot={
                            "input_rows": int(context.df.shape[0]),
                            "predictor_count": len(base_predictors),
                            "max_runs": boruta_result.max_runs,
                        },
                        output_summary={
                            "sample_size": boruta_result.sample_size,
                            "excluded_rows": boruta_result.excluded_rows,
                            "actual_runs": boruta_result.actual_runs,
                            "max_runs": boruta_result.max_runs,
                            "selected_predictor_count": len(context.predictors),
                            "confirmed_count": boruta_result.confirmed_count,
                            "rejected_count": boruta_result.rejected_count,
                        },
                        output_tables=[
                            {
                                "name": "boruta_features",
                                "columns": table_columns,
                                "rows": table_rows,
                            }
                        ],
                        output_plots=_plots_to_output_payload(boruta_result.plots),
                        artifacts=[
                            _artifact_from_bytes(
                                artifact_type="table",
                                name="Boruta 变量筛选结果",
                                filename=f"{dataset_name}_boruta_features.csv",
                                media_type="text/csv",
                                content=_table_csv_bytes(table_columns, table_rows),
                            ),
                        ],
                        logs=[
                            boruta_result.note,
                            f"selected_predictors={', '.join(context.predictors) if context.predictors else 'none'}",
                        ],
                        next_variable_set=context.predictors,
                    )
                )
                logs.append(f"Boruta 变量筛选节点 {node.label} 已执行，当前候选变量数 {len(context.predictors)}。")
        elif node.module_id == "feature-merge":
            if len(upstream_contexts) < 2:
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="skipped",
                        message="特征合并节点至少需要 2 个上游筛选结果",
                        details=["请将两个或以上的特征筛选节点连接到当前节点后再运行。"],
                    )
                )
                node_contexts[node.id] = context
                continue

            merge_rule = str(node.values.get("mergeRule") or "交集").strip() or "交集"
            min_votes_raw = str(node.values.get("minVotes") or "2").strip() or "2"
            try:
                min_votes = int(min_votes_raw)
            except ValueError as exc:
                raise BadRequest("特征合并节点的最少入选次数必须是有效整数") from exc

            upstream_labels = [
                f"{nodes_by_id[connection.from_node_id].label}({index + 1})"
                if connection.from_node_id in nodes_by_id else f"upstream_{index + 1}"
                for index, connection in enumerate(incoming_connections)
            ]
            merge_result = _merge_feature_sets(upstream_contexts, upstream_labels, merge_rule, min_votes)
            context.predictors = _clean_str_list(merge_result["selected_predictors"]) or context.predictors
            final_predictors = context.predictors
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message=f"特征合并已完成，当前保留 {len(context.predictors)} 个变量",
                    details=[
                        f"合并规则: {merge_rule}",
                        f"上游分支数: {merge_result['upstream_count']}",
                        f"实际阈值: 至少入选 {merge_result['effective_min_votes']} 次",
                    ],
                    input_snapshot={
                        "predictor_count": len(base_predictors),
                        "merge_rule": merge_rule,
                        "min_votes": min_votes,
                        "upstream_labels": upstream_labels,
                    },
                    output_summary={
                        "selected_predictor_count": len(context.predictors),
                        "upstream_count": merge_result["upstream_count"],
                        "effective_min_votes": merge_result["effective_min_votes"],
                    },
                    output_tables=[
                        {
                            "name": "feature_merge",
                            "columns": merge_result["table_columns"],
                            "rows": merge_result["table_rows"],
                        }
                    ],
                    artifacts=[
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="特征合并结果",
                            filename=f"{dataset_name}_feature_merge.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(merge_result["table_columns"], merge_result["table_rows"]),
                        )
                    ],
                    logs=[f"merged_predictors={', '.join(context.predictors) if context.predictors else 'none'}"],
                    next_variable_set=context.predictors,
                )
            )
            logs.append(f"特征合并节点 {node.label} 已执行，当前候选变量数 {len(context.predictors)}。")
        elif node.module_id in {"rcs", "interaction"}:
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="unsupported",
                    message="该特征工程节点的自动执行尚未接入",
                    details=[f"当前参数: {', '.join(f'{k}={v}' for k, v in node.values.items()) or '默认'}"],
                )
            )
        elif node.module_id == "logistic-model":
            if template_kind != "binary":
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="unsupported",
                        message="Logistic 模型仅支持二分类结局，请切换为二分类结局或改用其他分析工作台",
                    )
                )
                node_contexts[node.id] = context
                continue
            model_df, test_df, data_source_label = _resolve_model_input_frames(
                node=node,
                context=context,
                base_context=base_context,
                has_upstream=bool(incoming_connections),
            )
            if not outcome_variable or outcome_variable not in model_df.columns:
                raise BadRequest("当前 Logistic 模型节点缺少结局变量")
            if not _supports_binary_outcome(model_df[outcome_variable]):
                raise BadRequest("Logistic 回归要求二分类结局；当前选择的结局变量不是二分类")
            if data_source_label in {"原始数据", "测试集"}:
                context.holdout_frames = {}
            context.df = model_df
            predictors_for_model = context.predictors
            entry_mode = str(node.values.get("entry") or "筛选后进入")
            logistic_result = run_logistic_regression(
                df=model_df,
                dataset_name=dataset_name,
                outcome_variable=outcome_variable or "",
                predictor_variables=predictors_for_model,
                alpha=alpha,
                apply_univariate_screening=False,
                test_df=test_df,
                predictor_kind_overrides=context.kind_overrides,
            )
            context.logistic_result = logistic_result
            context.random_forest_model_result = None
            context.xgboost_model_result = None
            context.predictors = logistic_result.predictor_variables
            final_predictors = context.predictors
            multivariable_columns = ["term", "coefficient", "std_error", "odds_ratio", "conf_low", "conf_high", "p_value"]
            multivariable_rows = [
                [item.term, item.coefficient, item.std_error, item.odds_ratio, item.conf_low, item.conf_high, item.p_value]
                for item in logistic_result.coefficients
            ]
            performance_columns = ["dataset", "sample_size", "event_count", "auc", "accuracy", "sensitivity", "specificity", "precision", "npv", "f1", "brier_score", "hosmer_lemeshow_p_value"]
            performance_rows = [
                [item.dataset, item.sample_size, item.event_count, item.auc, item.accuracy, item.sensitivity, item.specificity, item.precision, item.npv, item.f1, item.brier_score, item.hosmer_lemeshow_p_value]
                for item in logistic_result.metrics
            ]
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message=f"Logistic 回归已完成，最终进入模型 {len(context.predictors)} 个变量",
                    details=[
                        f"样本量: {logistic_result.sample_size}",
                        f"Pseudo R²: {logistic_result.pseudo_r_squared if logistic_result.pseudo_r_squared is not None else 'NA'}",
                        f"AIC: {logistic_result.aic if logistic_result.aic is not None else 'NA'}",
                        f"H-L P: {logistic_result.hosmer_lemeshow_p_value if logistic_result.hosmer_lemeshow_p_value is not None else 'NA'}",
                    ],
                    input_snapshot={
                        "data_source": data_source_label,
                        "input_rows": int(model_df.shape[0]),
                        "predictors": predictors_for_model,
                        "selection": entry_mode,
                    },
                    output_summary={
                        "sample_size": logistic_result.sample_size,
                        "pseudo_r_squared": logistic_result.pseudo_r_squared,
                        "aic": logistic_result.aic,
                        "model_p_value": logistic_result.model_p_value,
                        "hosmer_lemeshow_p_value": logistic_result.hosmer_lemeshow_p_value,
                    },
                    output_tables=[
                        {
                            "name": "logistic_performance",
                            "columns": performance_columns,
                            "rows": performance_rows,
                        },
                        {
                            "name": "multivariable_logistic",
                            "columns": multivariable_columns,
                            "rows": multivariable_rows,
                        },
                    ],
                    output_plots=[],
                    artifacts=[
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="Logistic 模型性能表",
                            filename=f"{dataset_name}_logistic_performance.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(performance_columns, performance_rows),
                        ),
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="Logistic 多因素回归三线表",
                            filename=f"{dataset_name}_logistic_multivariable.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(multivariable_columns, multivariable_rows),
                        ),
                    ],
                    logs=["Logistic regression completed", f"final_predictors={len(context.predictors)}"],
                    next_variable_set=context.predictors,
                )
            )
            logs.append(f"Logistic 节点 {node.label} 已完成。")
        elif node.module_id == "cox-model":
            if template_kind != "survival":
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="unsupported",
                        message="Cox 模型仅支持生存结局，请检查当前结局类型与节点连接",
                    )
                )
                node_contexts[node.id] = context
                continue
            model_df, _, data_source_label = _resolve_model_input_frames(
                node=node,
                context=context,
                base_context=base_context,
                has_upstream=bool(incoming_connections),
            )
            if not time_variable or time_variable not in model_df.columns:
                raise BadRequest("当前 Cox 模型节点缺少时间变量")
            if not event_variable or event_variable not in model_df.columns:
                raise BadRequest("当前 Cox 模型节点缺少事件变量")
            if not _supports_binary_outcome(model_df[event_variable]):
                raise BadRequest("Cox 回归要求事件变量为二分类；当前事件变量不是二分类")
            time_numeric = pd.to_numeric(model_df[time_variable], errors="coerce").dropna()
            if time_numeric.empty or int(time_numeric.nunique(dropna=True)) < 2:
                raise BadRequest("Cox 回归要求时间变量为连续数值（且至少包含两个不同取值）")
            if float(time_numeric.min()) < 0:
                raise BadRequest("Cox 回归要求时间变量为非负数")
            if data_source_label in {"原始数据", "测试集"}:
                context.holdout_frames = {}
            context.df = model_df
            cox_result = run_cox_regression(
                df=model_df,
                dataset_name=dataset_name,
                time_variable=time_variable or "",
                event_variable=event_variable or "",
                predictor_variables=context.predictors,
                alpha=alpha,
                apply_univariate_screening=False,
                predictor_kind_overrides=context.kind_overrides,
            )
            context.cox_result = cox_result
            context.random_forest_model_result = None
            context.xgboost_model_result = None
            context.predictors = cox_result.predictor_variables
            final_predictors = context.predictors
            multivariable_columns = ["term", "coefficient", "std_error", "hazard_ratio", "conf_low", "conf_high", "p_value"]
            multivariable_rows = [
                [item.term, item.coefficient, item.std_error, item.hazard_ratio, item.conf_low, item.conf_high, item.p_value]
                for item in cox_result.coefficients
            ]
            ph_columns = ["term", "statistic", "df", "p_value"]
            ph_rows = [
                [item.term, item.statistic, item.df, item.p_value]
                for item in cox_result.proportional_hazards_tests
            ]
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message=f"Cox 回归已完成，最终进入模型 {len(context.predictors)} 个变量",
                    details=[
                        f"样本量: {cox_result.sample_size}",
                        f"事件数: {cox_result.event_count}",
                        f"C-index: {cox_result.concordance if cox_result.concordance is not None else 'NA'}",
                    ],
                    input_snapshot={
                        "data_source": data_source_label,
                        "input_rows": int(model_df.shape[0]),
                        "predictors": context.predictors,
                        "time_variable": time_variable,
                        "event_variable": event_variable,
                        "selection": str(node.values.get("entry") or "筛选后进入"),
                    },
                    output_summary={
                        "sample_size": cox_result.sample_size,
                        "event_count": cox_result.event_count,
                        "concordance": cox_result.concordance,
                        "global_ph_p_value": cox_result.global_ph_p_value,
                    },
                    output_tables=[
                        {
                            "name": "multivariable_cox",
                            "columns": multivariable_columns,
                            "rows": multivariable_rows,
                        },
                        {
                            "name": "cox_ph_test",
                            "columns": ph_columns,
                            "rows": ph_rows,
                        },
                    ],
                    output_plots=[],
                    artifacts=[
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="Cox 多因素回归三线表",
                            filename=f"{dataset_name}_cox_multivariable.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(multivariable_columns, multivariable_rows),
                        ),
                        _artifact_from_bytes(
                            artifact_type="table",
                            name="Cox 比例风险检验表",
                            filename=f"{dataset_name}_cox_ph_test.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(ph_columns, ph_rows),
                        ),
                    ],
                    logs=["Cox regression completed", f"final_predictors={len(context.predictors)}"],
                    next_variable_set=context.predictors,
                )
            )
            logs.append(f"Cox 节点 {node.label} 已完成。")
        elif node.module_id in {"xgboost", "random-forest"}:
            if template_kind != "binary":
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="unsupported",
                        message=f"{node.label} 当前仅支持二分类/连续型结局（不支持生存结局）",
                    )
                )
                node_contexts[node.id] = context
                continue
            if not outcome_variable:
                raise BadRequest("当前模型节点缺少结局变量")
            model_df, test_df, data_source_label = _resolve_model_input_frames(
                node=node,
                context=context,
                base_context=base_context,
                has_upstream=bool(incoming_connections),
            )
            if data_source_label in {"原始数据", "测试集"}:
                context.holdout_frames = {}
                test_df = None
            context.df = model_df
            if node.module_id == "random-forest":
                trees = _parse_int_value(node.values.get("trees"), 500, label="树数量")
                mtry = str(node.values.get("mtry") or "sqrt(p)").strip() or "sqrt(p)"
                seed = _parse_int_value(node.values.get("seed"), 2026, label="随机种子")
                model_result = run_random_forest_model(
                    df=model_df,
                    test_df=test_df,
                    dataset_name=dataset_name,
                    outcome_variable=outcome_variable,
                    predictor_variables=context.predictors,
                    trees=trees,
                    mtry=mtry,
                    seed=seed,
                    predictor_kind_overrides=context.kind_overrides,
                )
                context.random_forest_model_result = model_result
                context.xgboost_model_result = None
                random_forest_model_result = model_result
                detail_rows = [
                    [item.predictor, item.importance, item.secondary_importance, item.importance_scaled, item.rank]
                    for item in model_result.importance_rows
                ]
                output_summary = {
                    "sample_size": model_result.sample_size,
                    "trees": model_result.trees,
                    "mtry": model_result.mtry,
                    "oob_error_rate": model_result.oob_error_rate,
                    "task_kind": model_result.task_kind,
                }
                detail_text = [
                    f"样本量: {model_result.sample_size}",
                    f"树数量: {model_result.trees}",
                    f"mtry: {model_result.mtry}",
                    f"OOB error: {model_result.oob_error_rate if model_result.oob_error_rate is not None else 'NA'}",
                    f"任务类型: {'分类' if model_result.task_kind == 'classification' else '回归'}",
                ]
                message = f"随机森林模型已完成，当前输入 {len(context.predictors)} 个变量"
                artifact_prefix = "random_forest"
            else:
                eta = _parse_float_value(node.values.get("eta"), 0.05, label="学习率 eta")
                depth = _parse_int_value(node.values.get("depth"), 4, label="max_depth")
                rounds = _parse_int_value(node.values.get("rounds"), 300, label="nrounds")
                seed = _parse_int_value(node.values.get("seed"), 2026, label="随机种子")
                model_result = run_xgboost_model(
                    df=model_df,
                    test_df=test_df,
                    dataset_name=dataset_name,
                    outcome_variable=outcome_variable,
                    predictor_variables=context.predictors,
                    eta=eta,
                    depth=depth,
                    rounds=rounds,
                    seed=seed,
                    predictor_kind_overrides=context.kind_overrides,
                )
                context.xgboost_model_result = model_result
                context.random_forest_model_result = None
                xgboost_model_result = model_result
                detail_rows = [
                    [item.predictor, item.importance, item.secondary_importance, item.tertiary_importance, item.importance_scaled, item.rank]
                    for item in model_result.importance_rows
                ]
                output_summary = {
                    "sample_size": model_result.sample_size,
                    "eta": model_result.eta,
                    "max_depth": model_result.max_depth,
                    "nrounds": model_result.nrounds,
                    "task_kind": model_result.task_kind,
                }
                detail_text = [
                    f"样本量: {model_result.sample_size}",
                    f"eta: {model_result.eta}",
                    f"max_depth: {model_result.max_depth}",
                    f"nrounds: {model_result.nrounds}",
                    f"任务类型: {'分类' if model_result.task_kind == 'classification' else '回归'}",
                ]
                message = f"XGBoost 模型已完成，当前输入 {len(context.predictors)} 个变量"
                artifact_prefix = "xgboost"
            context.logistic_result = None
            context.cox_result = None
            final_predictors = context.predictors
            if model_result.task_kind == "regression":
                summary_columns = ["dataset", "sample_size", "rmse", "mae", "r_squared"]
                summary_rows = [[item.dataset, item.sample_size, item.rmse, item.mae, item.r_squared] for item in model_result.regression_metrics]
            else:
                summary_columns = ["dataset", "sample_size", "event_count", "auc", "accuracy", "sensitivity", "specificity", "precision", "npv", "f1", "brier_score", "hosmer_lemeshow_p_value"]
                summary_rows = [
                    [item.dataset, item.sample_size, item.event_count, item.auc, item.accuracy, item.sensitivity, item.specificity, item.precision, item.npv, item.f1, item.brier_score, item.hosmer_lemeshow_p_value]
                    for item in model_result.metrics
                ]
            detail_columns = (
                ["predictor", "importance", "secondary_importance", "importance_scaled", "rank"]
                if node.module_id == "random-forest"
                else ["predictor", "importance", "secondary_importance", "tertiary_importance", "importance_scaled", "rank"]
            )
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="completed",
                    message=message,
                    details=detail_text,
                    input_snapshot={
                        "data_source": data_source_label,
                        "input_rows": int(model_df.shape[0]),
                        "predictors": context.predictors,
                        "has_test_set": bool(test_df is not None and not test_df.empty),
                    },
                    output_summary=output_summary,
                    output_tables=[
                        {
                            "name": f"{artifact_prefix}_performance",
                            "columns": summary_columns,
                            "rows": summary_rows,
                        },
                        {
                            "name": f"{artifact_prefix}_importance",
                            "columns": detail_columns,
                            "rows": detail_rows,
                        },
                    ],
                    output_plots=[],
                    artifacts=[
                        _artifact_from_bytes(
                            artifact_type="table",
                            name=f"{node.label} 性能三线表",
                            filename=f"{dataset_name}_{artifact_prefix}_performance.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(summary_columns, summary_rows),
                        ),
                        _artifact_from_bytes(
                            artifact_type="table",
                            name=f"{node.label} 变量重要度表",
                            filename=f"{dataset_name}_{artifact_prefix}_importance.csv",
                            media_type="text/csv",
                            content=_table_csv_bytes(detail_columns, detail_rows),
                        ),
                    ],
                    logs=[model_result.note],
                    next_variable_set=context.predictors,
                )
            )
        elif node.module_id == "model-comparison":
            upstream_models = [
                source_id for source_id in [item.from_node_id for item in incoming_connections]
                if (
                    node_contexts.get(source_id)
                    and (
                        node_contexts[source_id].logistic_result
                        or node_contexts[source_id].cox_result
                        or node_contexts[source_id].random_forest_model_result
                        or node_contexts[source_id].xgboost_model_result
                    )
                )
            ]
            status = "configured" if upstream_models else "skipped"
            message = "模型比较节点已记录，待多模型比较引擎接入" if upstream_models else "当前无上游模型结果，模型比较节点未执行"
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status=status,
                    message=message,
                    details=[f"上游模型数: {len(upstream_models)}"],
                )
            )
        elif node.module_id in {"roc", "calibration", "dca", "bootstrap", "nomogram"}:
            upstream_model_node = _upstream_model_node(incoming_connections, nodes_by_id)
            if not upstream_model_node:
                node_results.append(
                    PipelineNodeStatusData(
                        node_id=node.id,
                        module_id=node.module_id,
                        label=node.label,
                        stage_id=node.stage_id,
                        status="skipped",
                        message="当前无上游模型结果，本节点未执行",
                    )
                )
            else:
                upstream_module_id = upstream_model_node.module_id
                model_type = _model_type_for_node(upstream_module_id)
                model_params = dict(upstream_model_node.values)
                test_df = context.holdout_frames.get("测试集")
                if node.module_id in {"roc", "calibration", "dca"}:
                    if not outcome_variable or outcome_variable not in context.df.columns:
                        node_results.append(
                            PipelineNodeStatusData(
                                node_id=node.id,
                                module_id=node.module_id,
                                label=node.label,
                                stage_id=node.stage_id,
                                status="skipped",
                                message="缺少结局变量，本节点未执行",
                            )
                        )
                        continue
                    if not _supports_binary_outcome(context.df[outcome_variable]):
                        node_results.append(
                            PipelineNodeStatusData(
                                node_id=node.id,
                                module_id=node.module_id,
                                label=node.label,
                                stage_id=node.stage_id,
                                status="unsupported",
                                message="ROC/校准/DCA 仅支持二分类结局；当前结局为连续型（回归任务）",
                            )
                        )
                        continue
                if node.module_id == "nomogram":
                    if model_type not in {"logistic", "cox"}:
                        node_results.append(
                            PipelineNodeStatusData(
                                node_id=node.id,
                                module_id=node.module_id,
                                label=node.label,
                                stage_id=node.stage_id,
                                status="unsupported",
                                message="列线图仅支持 Logistic 或 Cox 回归模型输入节点",
                            )
                        )
                    else:
                        scale_text = str(node.values.get("scale") or "100").strip()
                        scale_digits = "".join(char for char in scale_text if char.isdigit())
                        scale_points = int(scale_digits) if scale_digits else 100
                        scale_points = 200 if scale_points >= 200 else 100
                        timepoint_text = str(node.values.get("timepoint") or "").strip()
                        try:
                            nomogram_result = run_nomogram_plot(
                                train_df=context.df,
                                test_df=test_df,
                                dataset_name=dataset_name,
                                model_type="cox" if model_type == "cox" else "logistic",
                                outcome_variable=outcome_variable if model_type != "cox" else None,
                                time_variable=time_variable if model_type == "cox" else None,
                                event_variable=event_variable if model_type == "cox" else None,
                                predictor_variables=context.predictors,
                                scale_points=scale_points,
                                timepoint_text=timepoint_text,
                                model_params=model_params,
                                predictor_kind_overrides=context.kind_overrides,
                            )
                            train_m = nomogram_result.train_metrics
                            test_m = nomogram_result.test_metrics
                            summary_columns = ["dataset", "sample_size", "event_count", "auc", "brier_score", "c_index"]
                            summary_rows = [
                                [
                                    "训练集",
                                    train_m.sample_size,
                                    train_m.event_count,
                                    train_m.auc,
                                    train_m.brier_score,
                                    train_m.concordance,
                                ]
                            ]
                            if nomogram_result.has_test and test_m is not None:
                                summary_rows.append(
                                    [
                                        "测试集",
                                        test_m.sample_size,
                                        test_m.event_count,
                                        test_m.auc,
                                        test_m.brier_score,
                                        test_m.concordance,
                                    ]
                                )

                            fmt = lambda v: f"{v:.3f}" if v is not None else "NA"
                            detail_lines = [
                                f"模型类型: {'Cox' if model_type == 'cox' else 'Logistic'}",
                                f"总分刻度: {nomogram_result.scale_points}",
                            ]
                            if model_type == "cox" and nomogram_result.timepoint is not None:
                                detail_lines.append(f"预测时间点: {fmt(nomogram_result.timepoint)}")
                            if model_type == "logistic":
                                detail_lines.append(f"训练集 AUC: {fmt(train_m.auc)}")
                                if test_m is not None:
                                    detail_lines.append(f"测试集 AUC: {fmt(test_m.auc)}")
                            else:
                                detail_lines.append(f"训练集 C-index: {fmt(train_m.concordance)}")
                                if test_m is not None:
                                    detail_lines.append(f"测试集 C-index: {fmt(test_m.concordance)}")

                            node_results.append(
                                PipelineNodeStatusData(
                                    node_id=node.id,
                                    module_id=node.module_id,
                                    label=node.label,
                                    stage_id=node.stage_id,
                                    status="completed",
                                    message="列线图已生成（训练集 + 测试集）" if nomogram_result.has_test else "列线图已生成（训练集）",
                                    details=detail_lines,
                                    output_summary={
                                        "model_type": nomogram_result.model_type,
                                        "scale_points": nomogram_result.scale_points,
                                        "timepoint": nomogram_result.timepoint,
                                        "has_test": nomogram_result.has_test,
                                        "train_auc": train_m.auc,
                                        "test_auc": test_m.auc if test_m else None,
                                        "train_brier_score": train_m.brier_score,
                                        "test_brier_score": test_m.brier_score if test_m else None,
                                        "train_c_index": train_m.concordance,
                                        "test_c_index": test_m.concordance if test_m else None,
                                    },
                                    output_tables=[
                                        {"name": "nomogram_metrics", "columns": summary_columns, "rows": summary_rows},
                                    ],
                                    output_plots=_plots_to_output_payload(nomogram_result.plots),
                                    artifacts=[
                                        _artifact_from_bytes(
                                            artifact_type="table",
                                            name="列线图指标表",
                                            filename=f"{dataset_name}_{model_type}_nomogram_metrics.csv",
                                            media_type="text/csv",
                                            content=_table_csv_bytes(summary_columns, summary_rows),
                                        )
                                    ],
                                    logs=[nomogram_result.note],
                                    next_variable_set=context.predictors,
                                )
                            )
                        except Exception as nom_exc:
                            node_results.append(
                                PipelineNodeStatusData(
                                    node_id=node.id,
                                    module_id=node.module_id,
                                    label=node.label,
                                    stage_id=node.stage_id,
                                    status="failed",
                                    message=f"列线图执行失败: {nom_exc}",
                                    details=[str(nom_exc)],
                                )
                            )
                elif node.module_id in {"roc", "calibration", "dca"} and model_type == "cox":
                    node_results.append(
                        PipelineNodeStatusData(
                            node_id=node.id,
                            module_id=node.module_id,
                            label=node.label,
                            stage_id=node.stage_id,
                            status="unsupported",
                            message=f"{node.label} 当前仅支持二分类模型",
                        )
                    )
                elif node.module_id == "roc":
                    # Run the R script only for ROC curve plot generation
                    roc_result = run_roc_validation(
                        train_df=context.df,
                        test_df=test_df,
                        dataset_name=dataset_name,
                        model_type=model_type,
                        outcome_variable=outcome_variable or "",
                        predictor_variables=context.predictors,
                        ci_mode=str(node.values.get("ci") or "95% CI"),
                        cutoff_rule=str(node.values.get("cutoff") or "Youden index"),
                        model_params=model_params,
                        predictor_kind_overrides=context.kind_overrides,
                    )

                    # Build roc_summary rows from upstream model metrics when available
                    upstream_metrics: list[BinaryModelMetricData] = []
                    if model_type == "logistic" and context.logistic_result:
                        upstream_metrics = context.logistic_result.metrics
                    elif model_type == "random-forest" and context.random_forest_model_result:
                        upstream_metrics = context.random_forest_model_result.metrics
                    elif model_type == "xgboost" and context.xgboost_model_result:
                        upstream_metrics = context.xgboost_model_result.metrics

                    summary_columns = [
                        "evaluation_dataset", "sample_size", "event_count",
                        "auc", "auc_ci_low", "auc_ci_high", "youden_index", "threshold",
                        "accuracy", "sensitivity", "specificity", "precision",
                        "npv", "f1", "brier_score", "hosmer_lemeshow_p_value",
                    ]

                    if upstream_metrics:
                        # Use the authoritative metrics from the upstream model node
                        train_metric = next((m for m in upstream_metrics if m.dataset == "训练集"), None)
                        test_metric = next((m for m in upstream_metrics if m.dataset == "测试集"), None)

                        def _metric_row(label: str, m: BinaryModelMetricData | None, auc_ci_low: float | None, auc_ci_high: float | None, youden: float | None, threshold: float | None) -> list:
                            if m is None:
                                return [label, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
                            return [label, m.sample_size, m.event_count, m.auc, auc_ci_low, auc_ci_high, youden, threshold, m.accuracy, m.sensitivity, m.specificity, m.precision, m.npv, m.f1, m.brier_score, m.hosmer_lemeshow_p_value]

                        summary_rows = [
                            _metric_row("训练集", train_metric, roc_result.train_auc_ci_low, roc_result.train_auc_ci_high, roc_result.train_youden_index, roc_result.train_threshold),
                            _metric_row("测试集", test_metric, roc_result.test_auc_ci_low, roc_result.test_auc_ci_high, roc_result.test_youden_index, roc_result.test_threshold),
                        ]
                        train_auc_display = train_metric.auc if train_metric else None
                        test_auc_display = test_metric.auc if test_metric else None
                    else:
                        # Fallback: use ROC script's own metrics
                        summary_rows = [
                            ["训练集", roc_result.train_sample_size, roc_result.train_event_count, roc_result.train_auc, roc_result.train_auc_ci_low, roc_result.train_auc_ci_high, roc_result.train_youden_index, roc_result.train_threshold, roc_result.train_accuracy, roc_result.train_sensitivity, roc_result.train_specificity, roc_result.train_precision, roc_result.train_npv, roc_result.train_f1, roc_result.train_brier_score, None],
                            ["测试集", roc_result.test_sample_size, roc_result.test_event_count, roc_result.test_auc, roc_result.test_auc_ci_low, roc_result.test_auc_ci_high, roc_result.test_youden_index, roc_result.test_threshold, roc_result.test_accuracy, roc_result.test_sensitivity, roc_result.test_specificity, roc_result.test_precision, roc_result.test_npv, roc_result.test_f1, roc_result.test_brier_score, None],
                        ]
                        train_auc_display = roc_result.train_auc
                        test_auc_display = roc_result.test_auc

                    node_results.append(
                        PipelineNodeStatusData(
                            node_id=node.id,
                            module_id=node.module_id,
                            label=node.label,
                            stage_id=node.stage_id,
                            status="completed",
                            message=f"ROC / AUC 已完成（训练集 + 测试集）",
                            details=[
                                f"训练集 AUC: {train_auc_display if train_auc_display is not None else 'NA'}",
                                f"测试集 AUC: {test_auc_display if test_auc_display is not None else 'NA'}",
                                f"最佳阈值: {roc_result.threshold if roc_result.threshold is not None else 'NA'}",
                            ],
                            output_summary={"train_auc": train_auc_display, "test_auc": test_auc_display, "train_youden_index": roc_result.train_youden_index, "test_youden_index": roc_result.test_youden_index, "threshold": roc_result.threshold},
                            output_tables=[
                                {"name": "roc_summary", "columns": summary_columns, "rows": summary_rows},
                            ],
                            output_plots=_plots_to_output_payload(roc_result.plots),
                            artifacts=[],
                            logs=[roc_result.note],
                            next_variable_set=context.predictors,
                        )
                    )
                elif node.module_id == "calibration":
                    try:
                        calibration_result = run_calibration_validation(
                            train_df=context.df,
                            test_df=test_df,
                            dataset_name=dataset_name,
                            model_type=model_type,
                            outcome_variable=outcome_variable or "",
                            predictor_variables=context.predictors,
                            bins_mode=str(node.values.get("bins") or "Bootstrap 平滑"),
                            resamples=_parse_int_value(node.values.get("resamples"), 1000, label="重采样次数"),
                            model_params=model_params,
                            predictor_kind_overrides=context.kind_overrides,
                        )
                        train_m = calibration_result.train_metrics
                        test_m = calibration_result.test_metrics
                        summary_columns = ["dataset", "C-index", "Dxy", "Intercept", "Slope", "Emax", "Eavg", "Brier", "R2"]
                        summary_rows = [["训练集", train_m.c_index, train_m.dxy, train_m.intercept, train_m.slope, train_m.emax, train_m.eavg, train_m.brier, train_m.r2]]
                        if calibration_result.has_test and test_m is not None:
                            summary_rows.append(["测试集", test_m.c_index, test_m.dxy, test_m.intercept, test_m.slope, test_m.emax, test_m.eavg, test_m.brier, test_m.r2])
                        _fmt = lambda v: f"{v:.3f}" if v is not None else "NA"
                        node_results.append(
                            PipelineNodeStatusData(
                                node_id=node.id,
                                module_id=node.module_id,
                                label=node.label,
                                stage_id=node.stage_id,
                                status="completed",
                                message="校准曲线已完成（训练集 + 测试集）" if calibration_result.has_test else "校准曲线已完成（训练集）",
                                details=[f"训练集 Slope: {_fmt(train_m.slope)}, Brier: {_fmt(train_m.brier)}"] + ([f"测试集 Slope: {_fmt(test_m.slope)}, Brier: {_fmt(test_m.brier)}"] if test_m else []),
                                output_summary={
                                    "train_slope": train_m.slope,
                                    "train_intercept": train_m.intercept,
                                    "train_brier": train_m.brier,
                                    "train_c_index": train_m.c_index,
                                    "test_slope": test_m.slope if test_m else None,
                                    "test_intercept": test_m.intercept if test_m else None,
                                    "test_brier": test_m.brier if test_m else None,
                                    "test_c_index": test_m.c_index if test_m else None,
                                },
                                output_tables=[
                                    {"name": "calibration_summary", "columns": summary_columns, "rows": summary_rows},
                                ],
                                output_plots=_plots_to_output_payload(calibration_result.plots),
                                artifacts=[],
                                logs=[calibration_result.note],
                                next_variable_set=context.predictors,
                            )
                        )
                    except Exception as cal_exc:
                        node_results.append(
                            PipelineNodeStatusData(
                                node_id=node.id,
                                module_id=node.module_id,
                                label=node.label,
                                stage_id=node.stage_id,
                                status="failed",
                                message=f"校准曲线执行失败: {cal_exc}",
                                details=[str(cal_exc)],
                            )
                        )
                elif node.module_id == "dca":
                    dca_result = run_dca_validation(
                        train_df=context.df,
                        test_df=test_df,
                        dataset_name=dataset_name,
                        model_type=model_type,
                        outcome_variable=outcome_variable or "",
                        predictor_variables=context.predictors,
                        range_text=str(node.values.get("range") or "0.05 - 0.80"),
                        step=_parse_float_value(node.values.get("step"), 0.01, label="步长"),
                        model_params=model_params,
                        predictor_kind_overrides=context.kind_overrides,
                    )
                    summary_columns = ["evaluation_dataset", "threshold_min", "threshold_max", "threshold_step"]
                    summary_rows = [["训练集", dca_result.threshold_min, dca_result.threshold_max, dca_result.threshold_step]]
                    if dca_result.has_test:
                        summary_rows.append(["测试集", dca_result.threshold_min, dca_result.threshold_max, dca_result.threshold_step])

                    curve_columns = ["evaluation_dataset", "threshold", "model_net_benefit", "treat_all_net_benefit", "treat_none_net_benefit"]
                    curve_rows = [
                        ["训练集", item.threshold, item.model_net_benefit, item.treat_all_net_benefit, item.treat_none_net_benefit]
                        for item in dca_result.train_dca_rows
                    ]
                    if dca_result.test_dca_rows:
                        curve_rows.extend(
                            [
                                ["测试集", item.threshold, item.model_net_benefit, item.treat_all_net_benefit, item.treat_none_net_benefit]
                                for item in dca_result.test_dca_rows
                            ]
                        )
                    node_results.append(
                        PipelineNodeStatusData(
                            node_id=node.id,
                            module_id=node.module_id,
                            label=node.label,
                            stage_id=node.stage_id,
                            status="completed",
                            message="DCA 已完成（训练集 + 测试集）" if dca_result.has_test else "DCA 已完成（训练集）",
                            details=[
                                f"阈值范围: {dca_result.threshold_min} - {dca_result.threshold_max}",
                                f"步长: {dca_result.threshold_step}",
                            ]
                            + (["包含测试集曲线"] if dca_result.has_test else []),
                            output_summary={
                                "has_test": dca_result.has_test,
                                "threshold_min": dca_result.threshold_min,
                                "threshold_max": dca_result.threshold_max,
                            },
                            output_tables=[
                                {"name": "dca_summary", "columns": summary_columns, "rows": summary_rows},
                                {"name": "dca_curve", "columns": curve_columns, "rows": curve_rows},
                            ],
                            output_plots=_plots_to_output_payload(dca_result.plots),
                            artifacts=[
                                _artifact_from_bytes(
                                    artifact_type="table",
                                    name="DCA 结果表",
                                    filename=f"{dataset_name}_{model_type}_dca_curve.csv",
                                    media_type="text/csv",
                                    content=_table_csv_bytes(curve_columns, curve_rows),
                                )
                            ],
                            logs=[dca_result.note],
                            next_variable_set=context.predictors,
                        )
                    )
                else:
                    bootstrap_seed = _parse_int_value(node.values.get("seed"), 2026, label="随机种子")
                    bootstrap_resamples = _parse_int_value(node.values.get("resamples"), 1000, label="重采样次数")
                    bootstrap_result = run_bootstrap_validation(
                        train_df=context.df,
                        dataset_name=dataset_name,
                        model_type=model_type,
                        predictor_variables=context.predictors,
                        resamples=bootstrap_resamples,
                        seed=bootstrap_seed,
                        outcome_variable=outcome_variable if model_type != "cox" else None,
                        time_variable=time_variable if model_type == "cox" else None,
                        event_variable=event_variable if model_type == "cox" else None,
                        model_params=model_params,
                        predictor_kind_overrides=context.kind_overrides,
                    )
                    summary_columns = ["metric", "value"]
                    summary_rows = bootstrap_result.summary_rows
                    node_results.append(
                        PipelineNodeStatusData(
                            node_id=node.id,
                            module_id=node.module_id,
                            label=node.label,
                            stage_id=node.stage_id,
                            status="completed",
                            message=f"Bootstrap 已完成，校正后的 {bootstrap_result.metric_label} = {bootstrap_result.optimism_corrected_metric if bootstrap_result.optimism_corrected_metric is not None else 'NA'}",
                            details=[f"resamples: {bootstrap_result.requested_resamples}", f"completed: {bootstrap_result.completed_resamples}", f"seed: {bootstrap_result.seed}"],
                            output_summary={
                                "metric_label": bootstrap_result.metric_label,
                                "apparent_metric": bootstrap_result.apparent_metric,
                                "mean_optimism": bootstrap_result.mean_optimism,
                                "optimism_corrected_metric": bootstrap_result.optimism_corrected_metric,
                            },
                            output_tables=[
                                {"name": "bootstrap_summary", "columns": summary_columns, "rows": summary_rows},
                            ],
                            output_plots=_plots_to_output_payload(bootstrap_result.plots),
                            artifacts=[
                                _artifact_from_bytes(
                                    artifact_type="table",
                                    name="Bootstrap 结果表",
                                    filename=f"{dataset_name}_{model_type}_bootstrap_summary.csv",
                                    media_type="text/csv",
                                    content=_table_csv_bytes(summary_columns, summary_rows),
                                )
                            ],
                            logs=[bootstrap_result.note],
                            next_variable_set=context.predictors,
                        )
                    )
        else:
            node_results.append(
                PipelineNodeStatusData(
                    node_id=node.id,
                    module_id=node.module_id,
                    label=node.label,
                    stage_id=node.stage_id,
                    status="configured",
                    message="节点已识别，但当前引擎仅记录其配置，尚未接入真实执行逻辑",
                )
            )

        node_contexts[node.id] = context

    # --- Save execution cache for incremental runs (always, regardless of skip_completed) ---
    if dataset_id or workflow_id:
        existing_cache = _pipeline_run_cache.get(cache_key, {})
        result_by_node_id = {r.node_id: r for r in node_results}
        for node in ordered_nodes:
            ctx = node_contexts.get(node.id)
            res = result_by_node_id.get(node.id)
            if ctx and res and res.status == "completed":
                existing_cache[node.id] = (node_hashes[node.id], ctx, res)
        _pipeline_run_cache[cache_key] = existing_cache
        if skipped_count:
            logs.append(f"增量运行：已跳过 {skipped_count} 个未变更节点，直接复用上次执行结果。")

    effective_contexts = list(node_contexts.values()) or [base_context]
    preferred_contexts = [
        context for context in effective_contexts
        if context.logistic_result or context.cox_result or context.lasso_result or context.random_forest_model_result or context.xgboost_model_result
    ]
    final_df = (preferred_contexts[-1] if preferred_contexts else effective_contexts[-1]).df
    if int(final_df.shape[0]) <= 1:
        raise BadRequest("清洗后可用于分析的样本量不足")

    final_kind_overrides = (
        dict((preferred_contexts[-1] if preferred_contexts else effective_contexts[-1]).kind_overrides)
        if effective_contexts else dict(base_kind_overrides)
    )
    summary = _summarize_dataframe(final_df, final_kind_overrides)
    if not cleaning_operations:
        logs.append("本次运行未对数据执行显式缺失值处理节点，直接使用当前数据集参与建模。")

    if not lasso_result and nodes_by_module.get("lasso-selection"):
        engine_notes.append("LASSO 节点未实际执行，通常是因为它没有接在有效上游数据链路之后。")
    if not logistic_result and nodes_by_module.get("logistic-model"):
        engine_notes.append("Logistic 节点未实际执行，通常是因为它未接到有效的数据/特征链路。")
    if not cox_result and nodes_by_module.get("cox-model"):
        engine_notes.append("Cox 节点未实际执行，通常是因为它未接到有效的数据/特征链路。")
    if not random_forest_model_result and nodes_by_module.get("random-forest"):
        engine_notes.append("随机森林模型节点未实际执行，通常是因为它未接到有效的数据/特征链路。")
    if not xgboost_model_result and nodes_by_module.get("xgboost"):
        engine_notes.append("XGBoost 模型节点未实际执行，通常是因为它未接到有效的数据/特征链路。")

    engine_notes.extend([
        "当前高级分析流水线已支持按节点连线顺序执行：字段映射、缺失值处理、训练测试划分、分类变量编码、单因素筛选、VIF 共线性检查、LASSO、随机森林变量重要度、Boruta、特征合并、Logistic 回归、Cox 回归、随机森林建模、XGBoost、ROC、校准、DCA、Bootstrap。",
        "列线图仍未接入自动执行；报告节点当前输出为结构化文本摘要。",
    ])

    dataset_state = ClinicalPipelineDatasetStateData(
        dataset_name=dataset_name,
        original_rows=original_rows,
        original_columns=original_columns,
        analysis_rows=int(final_df.shape[0]),
        analysis_columns=int(final_df.shape[1]),
        cleaning_operations=cleaning_operations,
        summary=summary,
    )

    return ClinicalPipelineExecutionResult(
        template_kind=template_kind,
        dataset_state=dataset_state,
        final_predictors=final_predictors,
        node_results=node_results,
        logs=logs,
        engine_notes=engine_notes,
        lasso_result=lasso_result,
        logistic_result=logistic_result,
        cox_result=cox_result,
        random_forest_model_result=random_forest_model_result,
        xgboost_model_result=xgboost_model_result,
    )
