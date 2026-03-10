"""Prompt builders for regression interpretation."""

from __future__ import annotations

import json
from typing import Literal


def build_regression_system_prompt(language: Literal["zh", "en"]) -> str:
    if language == "en":
        return (
            "You are a senior medical biostatistics writing assistant. "
            "Write publication-ready Results prose for regression outputs in a medical research workflow. "
            "Use only the values explicitly provided in the JSON payload. "
            "Do not fabricate coefficients, P values, confidence intervals, causal claims, or clinical recommendations. "
            "Return only the Results-style narrative paragraph(s). "
            "Do not add headings, markdown, bullets, labels, section titles, or interpretation notes. "
            "Do not explain how to read coefficients, confidence intervals, or model metrics. "
            "Plain text only."
        )
    return (
        "你是一名医学统计写作助手，负责对回归分析结果做论文级结果解读。"
        "只能使用输入 JSON 中明确给出的统计量，不能编造系数、P 值、置信区间、因果结论或临床建议。"
        "输出只保留论文 Results/结果部分可直接使用的描述段落。"
        "不要添加标题、markdown、项目符号、标签、附注、解释说明或“如何解读结果”的赘述。"
        "不要解释系数、置信区间或模型指标代表什么。"
        "只输出纯文本。"
    )


def _selected_lasso_terms(payload: dict, selection_key: str) -> list[str]:
    terms: list[str] = []
    for item in payload.get("selected_features") or []:
        if item.get(selection_key):
            term = str(item.get("term") or "").strip()
            if term:
                terms.append(term)
    return terms


def _build_lasso_user_prompt(payload: dict, language: Literal["zh", "en"]) -> str:
    lambda_1se_terms = _selected_lasso_terms(payload, "selected_at_lambda_1se")
    lambda_min_terms = _selected_lasso_terms(payload, "selected_at_lambda_min")
    final_terms = lambda_1se_terms or lambda_min_terms
    final_rule = "lambda.1se" if lambda_1se_terms else "lambda.min"

    if language == "en":
        intro = (
            "Write exactly 1 paragraphs in plain text. "
            "It must be a concise Results paragraph for LASSO variable selection. "
            "State the sample size, outcome, family, lambda.min, lambda.1se, the number of retained non-zero variables, "
            f"and list only the variables retained in the final model selected by {final_rule}. "
            "Do not report coefficient values for individual variables and do not mention variables whose coefficients shrank to zero. "
            "Contain a figure legend close to this template: "
            '"Fig. 2. Presentation of the results of the LASSO regression analysis. '
            "(A) LASSO Regression Model Factor Selection: Left dashed line represents the optimal lambda value (lambda.min), "
            "while the right dashed line marks the lambda value within one standard error of the optimal (lambda.1se); "
            '(B) LASSO regression model screening variable trajectories." '
            "Do not add headings, bullets, markdown, or extra interpretation sections."
        )
    else:
        intro = (
            "请只输出1段纯文本。"
            "第一段写成 LASSO 变量筛选的 Results 结果段落：交代样本量、结局变量、family、lambda.min、lambda.1se、"
            f"最终模型采用 {final_rule} 规则保留的非零变量个数，并只列出最终系数不为 0 的变量名称。"
            "不要写各变量具体系数数值，不要提及系数收缩为 0 的变量。"
            "第二段写 Figure legend，并尽量贴近以下模板："
            '"Fig. 2. Presentation of the results of the LASSO regression analysis. '
            "(A) LASSO Regression Model Factor Selection: Left dashed line represents the optimal lambda value (lambda.min), "
            "while the right dashed line marks the lambda value within one standard error of the optimal (lambda.1se); "
            '(B) LASSO regression model screening variable trajectories." '
            "不要添加标题、markdown、项目符号或额外解释说明。"
        )

    return (
        f"{intro}\n\n"
        f"final_selection_rule: {final_rule}\n"
        f"final_nonzero_variables: {', '.join(final_terms) if final_terms else 'None'}\n"
        f"lambda_min_nonzero_variables: {', '.join(lambda_min_terms) if lambda_min_terms else 'None'}\n"
        f"lambda_1se_nonzero_variables: {', '.join(lambda_1se_terms) if lambda_1se_terms else 'None'}\n"
        f"lasso_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _build_logistic_user_prompt(payload: dict, language: Literal["zh", "en"]) -> str:
    if language == "en":
        intro = (
            "Write 1 compact Results paragraph in the style commonly used in high-quality medical journals. "
            "Do not write a teaching explanation. "
            "Focus on adjusted associations from the multivariable logistic regression model. "
            'Prefer wording such as "was independently associated with higher odds" or "was independently associated with lower odds". '
            "Report adjusted odds ratios as aOR with 95% CI and P values. "
            "For continuous predictors, describe the change per 1-unit increase unless the JSON explicitly specifies another unit. "
            "For binary or categorical predictors, interpret relative to the model reference level implied by the regression table. "
            "Do not mention pseudo R-squared, AIC, null deviance, residual deviance, or degrees of freedom in the paragraph unless explicitly required. "
            "Do not list every nonsignificant variable one by one unless needed for one brief closing sentence. "
            "Emphasize predictors that remained independently associated with the outcome after adjustment."
        )
    else:
        intro = (
            "请写成 1 段简洁、接近高质量医学期刊常见写法的 Results 结果段落。"
            "不要写教学式解释。"
            "重点写多因素 logistic 回归中经调整后的独立相关因素。"
            "优先使用“与结局发生几率升高独立相关”或“与结局发生几率降低独立相关”这类表述。"
            "请将 adjusted odds ratio 写成 aOR，并报告 95% CI 和 P 值。"
            "连续变量默认解释为每增加 1 个单位；二分类或多分类变量按回归表隐含的参考组进行表述。"
            "除非特别必要，不要在正文写 pseudo R²、AIC、null deviance、residual deviance 或自由度。"
            "不需要把所有无统计学意义的变量逐个罗列，最多用一句话简要收束。"
            "强调经调整后仍与结局独立相关的因素。"
        )

    return (
        f"{intro}\n\n"
        "Preferred structure:\n"
        "1. Briefly state the analytical sample and that a multivariable logistic regression model was fitted.\n"
        "2. Immediately report the predictors independently associated with the outcome.\n"
        "3. If useful, end with one short sentence stating that other covariates were not significantly associated.\n\n"
        f"logistic_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _build_cox_user_prompt(payload: dict, language: Literal["zh", "en"]) -> str:
    if language == "en":
        intro = (
            "Write 1 compact Results paragraph in the style commonly used in high-quality medical journals. "
            "Do not write a teaching explanation. "
            "Focus on the multivariable Cox proportional hazards regression model results. "
            "Report hazard ratios as HR with 95% CI and P values. "
            "Use only the compact regression table payload provided below. "
            "Mention the time-to-event outcome being modeled, emphasizing variables that significantly increase or decrease the hazard of the event. "
            "For continuous predictors, describe the effect per unit increase unless otherwise specified. "
            "Do not mention proportional hazards assumption tests, C-index, likelihood ratio statistics, formulas, excluded plots, or implementation details. "
            "Do not list every non-significant variable unless combining them in one brief concluding sentence. "
            "Emphasize independent predictors of the outcome over time."
        )
    else:
        intro = (
            "请写成 1 段简洁、接近高质量医学期刊常见写法的 Results 结果段落。"
            "不要写教学式解释。"
            "重点写多因素 Cox 比例风险回归模型结果。"
            "请将 hazard ratio 写成 HR，并报告 95% CI 和 P 值。"
            "只允许使用下方提供的紧凑回归三线表内容。"
            "写明生存时间结局，强调哪些变量显著增加或降低了事件发生的风险。"
            "连续变量默认解释为每增加 1 个单位；分类变量则与参考组对比。"
            "不要提及比例风险假设检验、C-index、似然比统计量、公式、图片或实现细节。"
            "不需要把所有无统计学意义的变量逐个罗列，最多用一句话概括。"
            "强调最终对时间-事件关联具有统计学意义的独立预测因素。"
        )

    return (
        f"{intro}\n\n"
        "Preferred structure:\n"
        "1. Briefly state the analytical sample, event counts, and that a Cox proportional hazards model was used.\n"
        "2. Immediately report the predictors independently associated with the hazard of the outcome.\n"
        "3. If useful, end with one short sentence stating that other covariates were not significantly associated.\n\n"
        f"cox_table_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def build_regression_user_prompt(
    analysis_kind: Literal["linear", "lasso", "logistic", "cox"],
    payload: dict,
    language: Literal["zh", "en"],
) -> str:
    if analysis_kind == "lasso":
        return _build_lasso_user_prompt(payload, language)
    if analysis_kind == "logistic":
        return _build_logistic_user_prompt(payload, language)
    if analysis_kind == "cox":
        return _build_cox_user_prompt(payload, language)

    if language == "en":
        intro = (
            "Write 1 to 2 compact Results paragraphs only. "
            "Start with sample size, model type, overall model significance, and key model-fit statistics when available. "
            "Then summarize the main statistically relevant findings using the provided estimates, confidence intervals, and P values. "
            "For logistic regression, interpret OR direction carefully. "
            "For lasso, summarize selected variables and lambda.min versus lambda.1se briefly as Results text only. "
            "Do not output any heading such as Results or Interpretation Note. "
            "Do not add explanatory teaching text."
        )
    else:
        intro = (
            "请只输出 1 段简洁的论文 Results 中文段落。"
            "先概述样本量、模型类型、整体模型显著性和关键拟合指标（如提供），再总结主要统计学结果。"
            "Logistic 回归需谨慎表述 OR 方向；LASSO 仅简要概述筛选变量和 lambda.min 与 lambda.1se 的结果。"
            "不要输出“Results”“Interpretation Note”等标题，不要写教学式解释，不要解释统计量含义。"
        )

    return (
        f"{intro}\n\n"
        f"analysis_kind: {analysis_kind}\n"
        f"regression_json:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
