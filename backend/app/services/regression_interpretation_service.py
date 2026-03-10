from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

from app.core.exceptions import BadRequest
from app.services.llm_client import request_chat_completion
from app.services.prompts.regression_prompts import (
    build_regression_system_prompt,
    build_regression_user_prompt,
)


FEATURE_NAME = 'AI回归解读'


@dataclass
class RegressionInterpretationResult:
    content: str
    model: str
    llm_tokens_used: int


def compact_regression_payload(
    analysis_kind: Literal['linear', 'lasso', 'logistic', 'cox'],
    payload: dict,
) -> dict:
    if analysis_kind == 'lasso':
        return {
            'dataset_name': payload.get('dataset_name'),
            'outcome_variable': payload.get('outcome_variable'),
            'family': payload.get('family'),
            'event_level': payload.get('event_level'),
            'reference_level': payload.get('reference_level'),
            'sample_size': payload.get('sample_size'),
            'excluded_rows': payload.get('excluded_rows'),
            'lambda_min': payload.get('lambda_min'),
            'lambda_1se': payload.get('lambda_1se'),
            'nonzero_count_lambda_min': payload.get('nonzero_count_lambda_min'),
            'nonzero_count_lambda_1se': payload.get('nonzero_count_lambda_1se'),
            'selected_features': [
                {
                    'term': row.get('term'),
                    'coefficient_lambda_min': row.get('coefficient_lambda_min'),
                    'coefficient_lambda_1se': row.get('coefficient_lambda_1se'),
                    'selected_at_lambda_min': row.get('selected_at_lambda_min'),
                    'selected_at_lambda_1se': row.get('selected_at_lambda_1se'),
                }
                for row in (payload.get('selected_features') or [])
                if isinstance(row, dict)
            ],
        }

    if analysis_kind == 'logistic':
        return {
            'dataset_name': payload.get('dataset_name'),
            'outcome_variable': payload.get('outcome_variable'),
            'event_level': payload.get('event_level'),
            'reference_level': payload.get('reference_level'),
            'sample_size': payload.get('sample_size'),
            'excluded_rows': payload.get('excluded_rows'),
            'model_p_value': payload.get('model_p_value'),
            'coefficients': [
                {
                    'term': row.get('term'),
                    'odds_ratio': row.get('odds_ratio'),
                    'conf_low': row.get('conf_low'),
                    'conf_high': row.get('conf_high'),
                    'p_value': row.get('p_value'),
                }
                for row in (payload.get('coefficients') or [])
                if isinstance(row, dict)
            ],
        }

    if analysis_kind == 'cox':
        return {
            'dataset_name': payload.get('dataset_name'),
            'time_variable': payload.get('time_variable'),
            'event_variable': payload.get('event_variable'),
            'event_level': payload.get('event_level'),
            'reference_level': payload.get('reference_level'),
            'sample_size': payload.get('sample_size'),
            'event_count': payload.get('event_count'),
            'excluded_rows': payload.get('excluded_rows'),
            'coefficients': [
                {
                    'term': row.get('term'),
                    'hazard_ratio': row.get('hazard_ratio'),
                    'conf_low': row.get('conf_low'),
                    'conf_high': row.get('conf_high'),
                    'p_value': row.get('p_value'),
                }
                for row in (payload.get('coefficients') or [])
                if isinstance(row, dict)
            ],
        }

    return {
        'dataset_name': payload.get('dataset_name'),
        'outcome_variable': payload.get('outcome_variable'),
        'sample_size': payload.get('sample_size'),
        'excluded_rows': payload.get('excluded_rows'),
        'r_squared': payload.get('r_squared'),
        'adjusted_r_squared': payload.get('adjusted_r_squared'),
        'model_p_value': payload.get('model_p_value'),
        'coefficients': [
            {
                'term': row.get('term'),
                'estimate': row.get('estimate'),
                'conf_low': row.get('conf_low'),
                'conf_high': row.get('conf_high'),
                'p_value': row.get('p_value'),
            }
            for row in (payload.get('coefficients') or [])
            if isinstance(row, dict)
        ],
    }


def build_regression_signature(analysis_kind: Literal['linear', 'lasso', 'logistic', 'cox'], payload: dict, language: Literal['zh', 'en']) -> str:
    compact_payload = compact_regression_payload(analysis_kind, payload)
    serialized = json.dumps(
        {
            'analysis_kind': analysis_kind,
            'payload': compact_payload,
            'language': language,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    )
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _strip_markdown_heading(text: str) -> str:
    stripped = text.strip()
    lines = stripped.splitlines()
    while lines:
        line = lines[0].strip()
        normalized = line.replace('*', '').replace('#', '').replace(':', '').strip().lower()
        if normalized in {'results', 'result', 'interpretation note', 'note'}:
            lines.pop(0)
            continue
        break
    return '\n'.join(lines).strip()


def _drop_extra_interpretation_sections(text: str) -> str:
    markers = [
        '\n**Interpretation Note',
        '\nInterpretation Note',
        '\n## Interpretation Note',
        '\n### Interpretation Note',
        '\n解释说明',
        '\n结果解释',
        '\n解读说明',
    ]
    content = text
    for marker in markers:
        index = content.find(marker)
        if index != -1:
            content = content[:index]
    return content.strip()


def _sanitize_interpretation_output(text: str) -> str:
    return _drop_extra_interpretation_sections(_strip_markdown_heading(text))


async def interpret_regression(
    analysis_kind: Literal['linear', 'lasso', 'logistic', 'cox'],
    payload: dict,
    language: Literal['zh', 'en'],
) -> RegressionInterpretationResult:
    compact_payload = compact_regression_payload(analysis_kind, payload)

    result = await request_chat_completion(
        messages=[
            {'role': 'system', 'content': build_regression_system_prompt(language)},
            {'role': 'user', 'content': build_regression_user_prompt(analysis_kind, compact_payload, language)},
        ],
        temperature=0.2,
        missing_key_message='AI 结果解读尚未配置模型 API Key',
        failure_message='AI 回归解读调用失败，请检查模型服务配置',
    )

    content = _sanitize_interpretation_output(result.content)
    if not content:
        raise BadRequest('AI 回归解读未返回有效内容')

    return RegressionInterpretationResult(
        content=content,
        model=result.model,
        llm_tokens_used=result.total_tokens,
    )
