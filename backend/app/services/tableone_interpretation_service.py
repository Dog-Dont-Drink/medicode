"""LLM-powered interpretation service for Table 1 baseline tables."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

import httpx

from app.core.config import get_settings
from app.core.exceptions import BadRequest
from app.schemas.descriptive import TableOneTablePayload


FEATURE_NAME = "AI结果解读"


@dataclass
class TableOneInterpretationResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def _serialize_table(table: TableOneTablePayload) -> str:
    lines = ["\t".join(table.headers)]
    for row in table.rows:
        padded_row = row + [""] * max(0, len(table.headers) - len(row))
        lines.append("\t".join(str(cell) for cell in padded_row[: len(table.headers)]))
    return "\n".join(lines)


def build_tableone_signature(table: TableOneTablePayload, language: Literal["zh", "en"]) -> str:
    payload = {
        "dataset_name": table.dataset_name,
        "group_variable": table.group_variable,
        "group_levels": table.group_levels,
        "headers": table.headers,
        "rows": table.rows,
        "continuous_variables": sorted(table.continuous_variables),
        "categorical_variables": sorted(table.categorical_variables),
        "nonnormal_variables": sorted(table.nonnormal_variables),
        "normality_method": table.normality_method,
        "language": language,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _build_system_prompt(language: Literal["zh", "en"]) -> str:
    if language == "en":
        return (
            "You are a senior medical biostatistics writing assistant. "
            "Write publication-ready Results prose for a medical SCI manuscript based on a baseline Table 1. "
            "Use only the values explicitly provided in the Table 1 input. "
            "Do not fabricate numbers, variables, interpretations, mechanisms, or causal claims. "
            "Avoid line-by-line listing. Synthesize the table into fluent academic narrative. "
            "Start with the cohort and group distribution, then summarize the main pattern of between-group differences. "
            "Emphasize statistically significant baseline imbalances first, and mention non-significant variables only briefly when useful for flow. "
            "If a result is not significant, describe it cautiously and compactly. "
            "Use polished academic English suitable for the Results section. "
            "Return plain text only, without bullets, headings, markdown, or prefatory phrases."
        )

    return (
        "你是一名资深医学统计写作助手，负责根据基线特征三线表撰写 SCI 医学论文 Results 部分的结果段落。"
        "只能使用输入表格中明确给出的变量、数值、百分比和 P 值，不得编造任何信息。"
        "仅做客观结果描述，不做机制推断、因果推断、临床建议或讨论性评论。"
        "不要逐项流水账罗列变量，而要整合成连贯、凝练、符合论文写作习惯的叙述。"
        "先概述样本量和分组情况，再归纳主要的组间差异模式，优先写有统计学差异的变量；"
        "无显著差异的变量只做必要且简短的补充。"
        "语言要符合医学论文写作习惯，输出纯文本，不要标题、不要项目符号、不要 markdown。"
    )


def _build_user_prompt(table: TableOneTablePayload, language: Literal["zh", "en"]) -> str:
    output_requirement = (
        "Write 1 to 2 compact, polished result paragraphs in English, suitable for an SCI manuscript Results section."
        if language == "en"
        else "请用中文写 1 到 2 段凝练、连贯的结果描述，语气符合 SCI 医学论文 Results 部分。"
    )
    additional_rules = (
        "Open with the cohort size and the grouping variable. "
        "Do not enumerate every row mechanically. Combine related findings into sentence-level synthesis. "
        "For continuous variables, preserve the summary format exactly as shown in the table. "
        "For categorical variables, report n (%) accurately. "
        "Report P values exactly as displayed; preserve '<0.001' when present. "
        "Prioritize statistically significant baseline differences, and limit non-significant findings to a short concluding sentence if needed. "
        "Avoid repeating the same sentence structure across variables. "
        "Do not explain statistical methods unless necessary in one short phrase."
        if language == "en"
        else "先交代总体样本量、分组变量和各组样本分布。"
        "不要按表格顺序逐条罗列，而要把相关结果整合成自然段落。"
        "连续变量保留表中原有统计摘要格式，分类变量准确写 n (%)。"
        "P 值按表格原样呈现，遇到 <0.001 时保持该写法。"
        "优先描述有统计学差异的变量，再用一句话简要收束无显著差异的代表性变量。"
        "避免反复使用完全相同的句式。"
        "除非非常必要，不要展开解释统计方法。"
    )

    return (
        f"{output_requirement}\n"
        f"{additional_rules}\n\n"
        f"Dataset: {table.dataset_name}\n"
        f"Grouping variable: {table.group_variable}\n"
        f"Group levels: {', '.join(table.group_levels)}\n"
        f"Continuous variables: {', '.join(table.continuous_variables) or 'None'}\n"
        f"Categorical variables: {', '.join(table.categorical_variables) or 'None'}\n"
        f"Non-normal variables: {', '.join(table.nonnormal_variables) or 'None'}\n"
        f"Normality assessment: {table.normality_method}\n\n"
        "Table 1 TSV:\n"
        f"{_serialize_table(table)}"
    )


async def interpret_tableone(table: TableOneTablePayload, language: Literal["zh", "en"]) -> TableOneInterpretationResult:
    settings = get_settings()
    if not settings.LLM_API_KEY.strip():
        raise BadRequest("AI 结果解读尚未配置模型 API Key")

    url = f"{settings.LLM_API_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.LLM_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": _build_system_prompt(language)},
            {"role": "user", "content": _build_user_prompt(table, language)},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = "AI 结果解读调用失败，请检查模型服务配置"
        try:
            payload = exc.response.json()
            message = payload.get("error", {}).get("message")
            if isinstance(message, str) and message.strip():
                detail = f"AI 结果解读调用失败: {message.strip()}"
        except ValueError:
            pass
        raise BadRequest(detail) from exc
    except httpx.HTTPError as exc:
        raise BadRequest("AI 结果解读调用失败，请检查模型服务配置") from exc

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    if isinstance(content, list):
        content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    content = str(content).strip()
    if not content:
        raise BadRequest("AI 结果解读未返回有效内容")

    model = str(data.get("model") or settings.LLM_MODEL)
    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))

    return TableOneInterpretationResult(
        content=content,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
