"""Prompt builders for grammar proofreading / academic polishing."""

from __future__ import annotations

import json

from app.schemas.polish import PolishStrength, SectionType, TextType


def build_grammar_system_prompt() -> str:
    return (
        "You are a senior medical scientific editor and language quality-control tool. "
        "Your task is NOT translation. You must improve grammar, spelling, punctuation, and academic tone for SCI manuscripts. "
        "Additionally, check and normalize scientific writing conventions when necessary: "
        "units (e.g., mg/dL, mmol/L), statistical reporting (e.g., P < 0.05, 95% CI, OR/HR formatting), and typography. "
        "Hard constraints:\n"
        "1) Do NOT change scientific meaning.\n"
        "2) Do NOT add new data, results, mechanisms, or conclusions.\n"
        "3) Preserve ALL numbers, units, p-values, confidence intervals, effect sizes, and statistical notation.\n"
        "4) Preserve gene names, drug names, abbreviations, and any placeholder tokens like __PROTECT_123__ exactly.\n"
        "5) Keep English output only.\n\n"
        "Return STRICT JSON only, without markdown, without extra commentary. "
        "JSON schema:\n"
        "{\n"
        '  "sentences": [\n'
        "    {\n"
        '      "index": 0,\n'
        '      "original": "...",\n'
        '      "revised": "...",\n'
        '      "changed": true,\n'
        '      "edit_types": ["grammar","spelling","punctuation","style"],\n'
        '      "reasons": ["...","..."],\n'
        '      "confidence": 0.0\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules for JSON:\n"
        "- Keep the same number of items as input.\n"
        "- Preserve the input 'original' exactly.\n"
        "- If no change is needed, set revised==original, changed=false, edit_types=[], reasons=[].\n"
        "- edit_types may include: grammar, spelling, punctuation, style, units, statistics.\n"
    )


def build_grammar_user_prompt(
    *,
    sentences: list[dict[str, str | int]],
    section_type: SectionType,
    text_type: TextType,
    strength: PolishStrength,
    protect_terms: bool,
    preserve_structure: bool,
) -> str:
    strength_rule = {
        "conservative": (
            "Mode: conservative correction. Fix grammar/spelling/punctuation only. "
            "Do NOT rewrite style unless necessary for correctness."
        ),
        "standard": (
            "Mode: standard academic polish. Fix grammar/spelling/punctuation and improve clarity/academic tone, "
            "but keep sentence structure largely intact."
        ),
        "deep": (
            "Mode: deep polish. Improve clarity and conciseness, split run-on sentences when needed, "
            "replace informal phrases with academic alternatives, while strictly preserving meaning."
        ),
    }[strength]

    structure_rule = (
        "Preserve original sentence structure as much as possible."
        if preserve_structure
        else "You may restructure sentences when it improves readability."
    )

    term_rule = (
        "Terminology protection is ON: do not change domain terms, gene/drug names, abbreviations, units, and statistical notation."
        if protect_terms
        else "Terminology protection is OFF: you may lightly normalize terms, but never alter numbers/units/statistics."
    )

    return (
        f"Section type: {section_type}\n"
        f"Text scope: {text_type}\n"
        f"{strength_rule}\n"
        f"{structure_rule}\n"
        f"{term_rule}\n\n"
        "Input sentences JSON:\n"
        f"{json.dumps(sentences, ensure_ascii=False, separators=(',', ':'))}\n"
    )
