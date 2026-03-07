from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from typing import Literal

import httpx

from app.core.config import get_settings
from app.core.exceptions import BadRequest


FEATURE_NAME = 'AI回归解读'
logger = logging.getLogger(__name__)


@dataclass
class RegressionInterpretationResult:
    content: str
    model: str
    llm_tokens_used: int


def build_regression_signature(analysis_kind: Literal['linear', 'lasso', 'logistic'], payload: dict, language: Literal['zh', 'en']) -> str:
    serialized = json.dumps(
        {
            'analysis_kind': analysis_kind,
            'payload': payload,
            'language': language,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    )
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _build_system_prompt(language: Literal['zh', 'en']) -> str:
    if language == 'en':
        return (
            'You are a senior medical biostatistics writing assistant. '
            'Write publication-ready Results prose for regression outputs in a medical research workflow. '
            'Use only the values explicitly provided in the JSON payload. '
            'Do not fabricate coefficients, P values, confidence intervals, causal claims, or clinical recommendations. '
            'Return only the Results-style narrative paragraph(s). '
            'Do not add headings, markdown, bullets, labels, section titles, or interpretation notes. '
            'Do not explain how to read coefficients, confidence intervals, or model metrics. '
            'Plain text only.'
        )
    return (
        '你是一名医学统计写作助手，负责对回归分析结果做论文级结果解读。'
        '只能使用输入 JSON 中明确给出的统计量，不能编造系数、P 值、置信区间、因果结论或临床建议。'
        '输出只保留论文 Results/结果部分可直接使用的描述段落。'
        '不要添加标题、markdown、项目符号、标签、附注、解释说明或“如何解读结果”的赘述。'
        '不要解释系数、置信区间或模型指标代表什么。'
        '只输出纯文本。'
    )


def _selected_lasso_terms(payload: dict, selection_key: str) -> list[str]:
    terms: list[str] = []
    for item in payload.get('selected_features') or []:
        if item.get(selection_key):
            term = str(item.get('term') or '').strip()
            if term:
                terms.append(term)
    return terms


def _build_lasso_user_prompt(payload: dict, language: Literal['zh', 'en']) -> str:
    lambda_1se_terms = _selected_lasso_terms(payload, 'selected_at_lambda_1se')
    lambda_min_terms = _selected_lasso_terms(payload, 'selected_at_lambda_min')
    final_terms = lambda_1se_terms or lambda_min_terms
    final_rule = 'lambda.1se' if lambda_1se_terms else 'lambda.min'

    if language == 'en':
        intro = (
            'Write exactly 2 paragraphs in plain text. '
            'Paragraph 1 must be a concise Results paragraph for LASSO variable selection. '
            'State the sample size, outcome, family, lambda.min, lambda.1se, the number of retained non-zero variables, '
            f'and list only the variables retained in the final model selected by {final_rule}. '
            'Do not report coefficient values for individual variables and do not mention variables whose coefficients shrank to zero. '
            'Paragraph 2 must be a figure legend close to this template: '
            '"Fig. 2. Presentation of the results of the LASSO regression analysis. '
            '(A) LASSO Regression Model Factor Selection: Left dashed line represents the optimal lambda value (lambda.min), '
            'while the right dashed line marks the lambda value within one standard error of the optimal (lambda.1se); '
            '(B) LASSO regression model screening variable trajectories." '
            'Do not add headings, bullets, markdown, or extra interpretation sections.'
        )
    else:
        intro = (
            '请只输出 2 段纯文本。'
            '第一段写成 LASSO 变量筛选的 Results 结果段落：交代样本量、结局变量、family、lambda.min、lambda.1se、'
            f'最终模型采用 {final_rule} 规则保留的非零变量个数，并只列出最终系数不为 0 的变量名称。'
            '不要写各变量具体系数数值，不要提及系数收缩为 0 的变量。'
            '第二段写 Figure legend，并尽量贴近以下模板：'
            '"Fig. 2. Presentation of the results of the LASSO regression analysis. '
            '(A) LASSO Regression Model Factor Selection: Left dashed line represents the optimal lambda value (lambda.min), '
            'while the right dashed line marks the lambda value within one standard error of the optimal (lambda.1se); '
            '(B) LASSO regression model screening variable trajectories." '
            '不要添加标题、markdown、项目符号或额外解释说明。'
        )

    return (
        f'{intro}\n\n'
        f'final_selection_rule: {final_rule}\n'
        f'final_nonzero_variables: {", ".join(final_terms) if final_terms else "None"}\n'
        f'lambda_min_nonzero_variables: {", ".join(lambda_min_terms) if lambda_min_terms else "None"}\n'
        f'lambda_1se_nonzero_variables: {", ".join(lambda_1se_terms) if lambda_1se_terms else "None"}\n'
        f'lasso_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}'
    )


def _build_logistic_user_prompt(payload: dict, language: Literal['zh', 'en']) -> str:
    if language == 'en':
        intro = (
            'Write 1 compact Results paragraph in the style commonly used in high-quality medical journals. '
            'Do not write a teaching explanation. '
            'Focus on adjusted associations from the multivariable logistic regression model. '
            'Prefer wording such as "was independently associated with higher odds" or "was independently associated with lower odds". '
            'Report adjusted odds ratios as aOR with 95% CI and P values. '
            'For continuous predictors, describe the change per 1-unit increase unless the JSON explicitly specifies another unit. '
            'For binary or categorical predictors, interpret relative to the model reference level implied by the regression table. '
            'Do not mention pseudo R-squared, AIC, null deviance, residual deviance, or degrees of freedom in the paragraph unless explicitly required. '
            'Do not list every nonsignificant variable one by one unless needed for one brief closing sentence. '
            'Emphasize predictors that remained independently associated with the outcome after adjustment.'
        )
    else:
        intro = (
            '请写成 1 段简洁、接近高质量医学期刊常见写法的 Results 结果段落。'
            '不要写教学式解释。'
            '重点写多因素 logistic 回归中经调整后的独立相关因素。'
            '优先使用“与结局发生几率升高独立相关”或“与结局发生几率降低独立相关”这类表述。'
            '请将 adjusted odds ratio 写成 aOR，并报告 95% CI 和 P 值。'
            '连续变量默认解释为每增加 1 个单位；二分类或多分类变量按回归表隐含的参考组进行表述。'
            '除非特别必要，不要在正文写 pseudo R²、AIC、null deviance、residual deviance 或自由度。'
            '不需要把所有无统计学意义的变量逐个罗列，最多用一句话简要收束。'
            '强调经调整后仍与结局独立相关的因素。'
        )

    return (
        f'{intro}\n\n'
        'Preferred structure:\n'
        '1. Briefly state the analytical sample and that a multivariable logistic regression model was fitted.\n'
        '2. Immediately report the predictors independently associated with the outcome.\n'
        '3. If useful, end with one short sentence stating that other covariates were not significantly associated.\n\n'
        f'logistic_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}'
    )


def _build_user_prompt(analysis_kind: Literal['linear', 'lasso', 'logistic'], payload: dict, language: Literal['zh', 'en']) -> str:
    if analysis_kind == 'lasso':
        return _build_lasso_user_prompt(payload, language)
    if analysis_kind == 'logistic':
        return _build_logistic_user_prompt(payload, language)

    if language == 'en':
        intro = (
            'Write 1 to 2 compact Results paragraphs only. '
            'Start with sample size, model type, overall model significance, and key model-fit statistics when available. '
            'Then summarize the main statistically relevant findings using the provided estimates, confidence intervals, and P values. '
            'For logistic regression, interpret OR direction carefully. '
            'For lasso, summarize selected variables and lambda.min versus lambda.1se briefly as Results text only. '
            'Do not output any heading such as Results or Interpretation Note. '
            'Do not add explanatory teaching text.'
        )
    else:
        intro = (
            '请只输出 1 到 2 段简洁的论文 Results 中文段落。'
            '先概述样本量、模型类型、整体模型显著性和关键拟合指标（如提供），再总结主要统计学结果。'
            'Logistic 回归需谨慎表述 OR 方向；LASSO 仅简要概述筛选变量和 lambda.min 与 lambda.1se 的结果。'
            '不要输出“Results”“Interpretation Note”等标题，不要写教学式解释，不要解释统计量含义。'
        )

    return (
        f'{intro}\n\n'
        f'analysis_kind: {analysis_kind}\n'
        f'regression_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}'
    )


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
    analysis_kind: Literal['linear', 'lasso', 'logistic'],
    payload: dict,
    language: Literal['zh', 'en'],
) -> RegressionInterpretationResult:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.LLM_API_KEY.strip():
        logger.warning('LLM API key is empty for regression interpretation')
        raise BadRequest('AI 结果解读尚未配置模型 API Key')

    url = f"{settings.LLM_API_BASE_URL.rstrip('/')}/chat/completions"
    body = {
        'model': settings.LLM_MODEL,
        'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': _build_system_prompt(language)},
            {'role': 'user', 'content': _build_user_prompt(analysis_kind, payload, language)},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers={
                    'Authorization': f'Bearer {settings.LLM_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json=body,
            )
            response.raise_for_status()
        
    except httpx.HTTPStatusError as exc:
        detail = 'AI 回归解读调用失败，请检查模型服务配置'
        try:
            error_payload = exc.response.json()
            message = error_payload.get('error', {}).get('message')
            if isinstance(message, str) and message.strip():
                detail = f'AI 回归解读调用失败: {message.strip()}'
        except ValueError:
            pass
        raise BadRequest(detail) from exc
    except httpx.HTTPError as exc:
        raise BadRequest('AI 回归解读调用失败，请检查模型服务配置') from exc

    data = response.json()
    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    if isinstance(content, list):
        content = ''.join(str(item.get('text', '')) for item in content if isinstance(item, dict))
    content = _sanitize_interpretation_output(str(content))
    if not content:
        raise BadRequest('AI 回归解读未返回有效内容')

    usage = data.get('usage') or {}
    llm_tokens_used = int(usage.get('total_tokens') or ((usage.get('prompt_tokens') or 0) + (usage.get('completion_tokens') or 0)))

    return RegressionInterpretationResult(
        content=content,
        model=str(data.get('model') or settings.LLM_MODEL),
        llm_tokens_used=llm_tokens_used,
    )
