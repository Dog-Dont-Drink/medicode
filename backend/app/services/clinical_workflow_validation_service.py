"""Workflow validation for the clinical model builder."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Literal, Protocol


StageId = Literal[
    "data-preparation",
    "feature-processing",
    "model-development",
    "model-validation",
]


STAGE_ORDER: dict[StageId, int] = {
    "data-preparation": 0,
    "feature-processing": 1,
    "model-development": 2,
    "model-validation": 3,
}

MODULE_STAGE: dict[str, StageId] = {
    "field-mapping": "data-preparation",
    "missing-value": "data-preparation",
    "split": "data-preparation",
    "encoding": "data-preparation",
    "univariate-screen": "feature-processing",
    "vif": "feature-processing",
    "lasso-selection": "feature-processing",
    "rf-importance": "feature-processing",
    "boruta-selection": "feature-processing",
    "feature-merge": "feature-processing",
    "rcs": "model-validation",
    "interaction": "feature-processing",
    "logistic-model": "model-development",
    "cox-model": "model-development",
    "xgboost": "model-development",
    "random-forest": "model-development",
    "model-comparison": "model-development",
    "roc": "model-validation",
    "calibration": "model-validation",
    "dca": "model-validation",
    "bootstrap": "model-validation",
    "nomogram": "model-validation",
}

ENTRY_MODULES = {"field-mapping", "missing-value", "split", "encoding"}
SINGLE_INPUT_MODULES = {
    "missing-value",
    "split",
    "encoding",
    "univariate-screen",
    "vif",
    "lasso-selection",
    "rf-importance",
    "boruta-selection",
    "rcs",
    "interaction",
    "logistic-model",
    "cox-model",
    "xgboost",
    "random-forest",
    "roc",
    "calibration",
    "dca",
    "bootstrap",
    "nomogram",
}


class WorkflowNodeLike(Protocol):
    id: str
    module_id: str
    label: str
    stage_id: str
    values: dict[str, str]


class WorkflowConnectionLike(Protocol):
    id: str
    from_node_id: str
    to_node_id: str


@dataclass
class WorkflowValidationIssue:
    severity: Literal["error", "warning"]
    code: str
    message: str
    node_id: str | None = None
    connection_id: str | None = None


@dataclass
class WorkflowValidationResult:
    issues: list[WorkflowValidationIssue] = field(default_factory=list)
    root_node_ids: list[str] = field(default_factory=list)
    leaf_node_ids: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(item.severity == "error" for item in self.issues)


def _required_field_map(module_id: str) -> list[tuple[str, str]]:
    if module_id == "field-mapping":
        return [("idField", "ID 字段"), ("outcomeField", "结局字段"), ("timeField", "时间字段")]
    if module_id == "missing-value":
        return [("method", "处理方式"), ("threshold", "缺失比例阈值")]
    if module_id == "split":
        return [("ratio", "划分比例"), ("sampling", "抽样方式"), ("seed", "随机种子")]
    if module_id == "encoding":
        return [("encoding", "编码方式"), ("dropFirst", "首列丢弃")]
    if module_id == "univariate-screen":
        return [("rule", "筛选规则"), ("keepClinical", "保留临床变量")]
    if module_id == "vif":
        return [("cutoff", "VIF 阈值")]
    if module_id == "lasso-selection":
        return [("criterion", "Lambda 规则"), ("folds", "交叉验证折数")]
    if module_id == "rf-importance":
        return [("trees", "树数量"), ("topN", "保留变量数")]
    if module_id == "boruta-selection":
        return [("maxRuns", "最大迭代次数")]
    if module_id == "feature-merge":
        return [("mergeRule", "合并规则"), ("minVotes", "最少入选次数")]
    if module_id == "rcs":
        return [("target", "目标变量"), ("knots", "节点数")]
    if module_id == "interaction":
        return [("pair", "交互项"), ("centering", "变量中心化")]
    if module_id == "logistic-model":
        return [("entry", "变量进入策略"), ("reference", "参考水平"), ("ci", "置信区间")]
    if module_id == "cox-model":
        return [("entry", "变量进入策略"), ("ties", "Ties 处理")]
    if module_id == "xgboost":
        return [("eta", "学习率 eta"), ("depth", "max_depth"), ("rounds", "nrounds"), ("seed", "随机种子")]
    if module_id == "random-forest":
        return [("trees", "树数量"), ("mtry", "mtry"), ("seed", "随机种子")]
    if module_id == "model-comparison":
        return [("primaryMetric", "主指标"), ("rankRule", "排序规则")]
    if module_id == "roc":
        return [("ci", "区间估计"), ("cutoff", "最佳截点规则")]
    if module_id == "calibration":
        return [("bins", "分组策略"), ("resamples", "重采样次数")]
    if module_id == "dca":
        return [("range", "阈值范围"), ("step", "步长")]
    if module_id == "bootstrap":
        return [("resamples", "重采样次数"), ("seed", "随机种子")]
    if module_id == "nomogram":
        return [("scale", "总分刻度"), ("timepoint", "预测时间点")]
    return []


def _conditional_required_labels(node: WorkflowNodeLike) -> list[str]:
    if node.module_id != "split":
        return []

    sampling = str(node.values.get("sampling", "")).strip()
    labels: list[str] = []
    if sampling == "分层抽样" and not str(node.values.get("stratifyField", "")).strip():
        labels.append("分层变量")
    if sampling == "时间切分" and not str(node.values.get("timeSplitField", "")).strip():
        labels.append("时间切分字段")
    return labels


def _validate_connection(
    source: WorkflowNodeLike,
    target: WorkflowNodeLike,
    existing_connections: list[WorkflowConnectionLike],
) -> str | None:
    if source.id == target.id:
        return "同一个节点不能连接自己。"

    source_stage_order = STAGE_ORDER.get(source.stage_id) or 0
    target_stage_order = STAGE_ORDER.get(target.stage_id) or 0
    if source_stage_order > target_stage_order:
        return "流程不能反向连接到前面的阶段。"

    if SINGLE_INPUT_MODULES.__contains__(target.module_id):
        if any(item.to_node_id == target.id and item.from_node_id != source.id for item in existing_connections):
            return "该节点当前只允许保留一个上游输入。"

    if target.stage_id == "model-validation" and source.stage_id != "model-development":
        return "验证类节点只能接在模型开发节点后面。"

    if target.module_id == "rcs" and source.module_id not in {"logistic-model", "cox-model"}:
        return "限制性立方样条只能接在 Logistic 或 Cox 模型后面。"

    if target.module_id == "nomogram" and source.module_id not in {"logistic-model", "cox-model"}:
        return "列线图只能接在 Logistic 或 Cox 模型后面。"

    if target.module_id == "bootstrap" and source.stage_id != "model-development":
        return "Bootstrap 需要直接接在模型开发节点后。"

    return None


def validate_clinical_workflow(
    nodes: list[WorkflowNodeLike],
    connections: list[WorkflowConnectionLike],
) -> WorkflowValidationResult:
    result = WorkflowValidationResult()
    if not nodes:
        result.issues.append(WorkflowValidationIssue(severity="error", code="empty_workflow", message="流程中至少需要一个节点。"))
        return result

    node_map: dict[str, WorkflowNodeLike] = {}
    module_counts: dict[str, int] = defaultdict(int)
    incoming_count: dict[str, int] = defaultdict(int)
    outgoing_count: dict[str, int] = defaultdict(int)

    for node in nodes:
        if node.id in node_map:
            result.issues.append(
                WorkflowValidationIssue(severity="error", code="duplicate_node_id", message=f"节点 {node.label} 存在重复 id。", node_id=node.id)
            )
            continue
        node_map[node.id] = node
        module_counts[node.module_id] += 1

        expected_stage = MODULE_STAGE.get(node.module_id)
        if not expected_stage:
            result.issues.append(
                WorkflowValidationIssue(severity="error", code="unknown_module", message=f"未知模块: {node.module_id}。", node_id=node.id)
            )
            continue
        if node.stage_id != expected_stage:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="error",
                    code="stage_mismatch",
                    message=f"节点 {node.label} 的阶段应为 {expected_stage}，当前为 {node.stage_id}。",
                    node_id=node.id,
                )
            )

        missing_labels = [
            label
            for key, label in _required_field_map(node.module_id)
            if not str(node.values.get(key, "")).strip()
        ]
        missing_labels.extend(_conditional_required_labels(node))
        if missing_labels:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="warning",
                    code="missing_node_values",
                    message=f"节点 {node.label} 仍有参数未配置完整：{', '.join(missing_labels)}。",
                    node_id=node.id,
                )
            )

    seen_pairs: set[tuple[str, str]] = set()
    adjacency: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {node_id: 0 for node_id in node_map}

    for connection in connections:
        source = node_map.get(connection.from_node_id)
        target = node_map.get(connection.to_node_id)
        if not source or not target:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="error",
                    code="dangling_connection",
                    message="存在指向无效节点的连线。",
                    connection_id=connection.id,
                )
            )
            continue

        pair = (source.id, target.id)
        if pair in seen_pairs:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="error",
                    code="duplicate_connection",
                    message="这两个节点之间存在重复连线。",
                    connection_id=connection.id,
                )
            )
            continue
        seen_pairs.add(pair)

        message = _validate_connection(source, target, connections)
        if message:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="error",
                    code="invalid_connection",
                    message=message,
                    connection_id=connection.id,
                )
            )
            continue

        adjacency[source.id].append(target.id)
        indegree[target.id] = indegree.get(target.id, 0) + 1
        incoming_count[target.id] += 1
        outgoing_count[source.id] += 1

    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    visited = 0
    indegree_copy = dict(indegree)
    while queue:
        node_id = queue.popleft()
        visited += 1
        for target_id in adjacency.get(node_id, []):
            indegree_copy[target_id] -= 1
            if indegree_copy[target_id] == 0:
                queue.append(target_id)

    if visited != len(node_map):
        result.issues.append(
            WorkflowValidationIssue(
                severity="error",
                code="cyclic_workflow",
                message="当前流程存在环路，无法执行。请移除循环连线。",
            )
        )

    for node in nodes:
        if node.module_id not in ENTRY_MODULES and incoming_count[node.id] == 0:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="warning",
                    code="missing_upstream",
                    message=f"节点 {node.label} 缺少上游输入。",
                    node_id=node.id,
                )
            )
        if node.module_id == "feature-merge" and incoming_count[node.id] < 2:
            result.issues.append(
                WorkflowValidationIssue(
                    severity="warning",
                    code="merge_inputs_insufficient",
                    message=f"节点 {node.label} 建议至少连接 2 个上游特征筛选节点。",
                    node_id=node.id,
                )
            )

    if module_counts.get("logistic-model", 0) + module_counts.get("cox-model", 0) + module_counts.get("xgboost", 0) + module_counts.get("random-forest", 0) == 0:
        result.issues.append(
            WorkflowValidationIssue(
                severity="warning",
                code="missing_model_node",
                message="当前流程尚未包含模型开发节点。",
            )
        )

    result.root_node_ids = [node_id for node_id in node_map if incoming_count[node_id] == 0]
    result.leaf_node_ids = [node_id for node_id in node_map if outgoing_count[node_id] == 0]
    return result
