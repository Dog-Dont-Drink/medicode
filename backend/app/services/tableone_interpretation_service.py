"""LLM-powered interpretation service for Table 1 baseline tables."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

from app.core.exceptions import BadRequest
from app.schemas.descriptive import TableOneTablePayload
from app.services.llm_client import request_chat_completion
from app.services.prompts.tableone_prompts import (
    build_tableone_system_prompt,
    build_tableone_user_prompt,
)


FEATURE_NAME = "AI结果解读"


@dataclass
class TableOneInterpretationResult:
    content: str
    model: str
    llm_tokens_used: int


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


async def interpret_tableone(table: TableOneTablePayload, language: Literal["zh", "en"]) -> TableOneInterpretationResult:
    result = await request_chat_completion(
        messages=[
            {"role": "system", "content": build_tableone_system_prompt(language)},
            {"role": "user", "content": build_tableone_user_prompt(table, language)},
        ],
        temperature=0.2,
        missing_key_message="AI 结果解读尚未配置模型 API Key",
        failure_message="AI 结果解读调用失败，请检查模型服务配置",
    )

    if not result.content:
        raise BadRequest("AI 结果解读未返回有效内容")

    return TableOneInterpretationResult(
        content=result.content,
        model=result.model,
        llm_tokens_used=result.total_tokens,
    )
