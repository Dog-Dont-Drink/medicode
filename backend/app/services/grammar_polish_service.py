"""Grammar proofreading & academic polish service backed by the configured LLM."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from app.core.exceptions import BadRequest
from app.schemas.polish import PolishStrength, SectionType, TextType
from app.services.llm_client import request_chat_completion
from app.services.prompts.grammar_polish_prompts import build_grammar_system_prompt, build_grammar_user_prompt


FEATURE_NAME = "语法校订"


@dataclass(frozen=True)
class SentenceEdit:
    index: int
    suffix: str
    original: str
    revised: str
    changed: bool
    edit_types: list[str]
    reasons: list[str]
    confidence: float | None


@dataclass(frozen=True)
class GrammarPolishResult:
    revised_text: str
    edits: list[SentenceEdit]
    model: str
    llm_tokens_used: int


_UNIT_PATTERNS = [
    r"\bmg/dL\b",
    r"\bmmol/L\b",
    r"\bmmHg\b",
    r"\bkg/m\^2\b",
    r"\bkg/m²\b",
]

_STAT_PATTERNS = [
    r"\bP\s*[<=>]\s*0?\.\d+\b",
    r"\bP\s*<\s*0\.001\b",
    r"\b\d+\s*%\s*CI\b",
    r"\b(?:OR|HR|RR)\s*=?\s*\d+(?:\.\d+)?\b",
    r"\b(?:AUC|C-index|CI)\b",
]

_NUMBER_PATTERN = r"\b\d+(?:\.\d+)?\b"

_PROTECT_PATTERN = re.compile(
    "("
    + "|".join(_UNIT_PATTERNS + _STAT_PATTERNS + [_NUMBER_PATTERN])
    + ")",
    flags=re.IGNORECASE,
)


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise BadRequest("语法校订返回内容不是有效 JSON")
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise BadRequest("语法校订返回内容解析失败，请稍后重试") from exc


def protect_special_tokens(text: str) -> tuple[str, dict[str, str]]:
    """Replace numbers/units/stat tokens with placeholders to prevent accidental edits."""
    mapping: dict[str, str] = {}
    if not text.strip():
        return text, mapping

    def _replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        key = f"__PROTECT_{len(mapping) + 1}__"
        mapping[key] = raw
        return key

    protected = _PROTECT_PATTERN.sub(_replace, text)
    return protected, mapping


def restore_special_tokens(text: str, mapping: dict[str, str]) -> str:
    restored = text
    for key, raw in mapping.items():
        restored = restored.replace(key, raw)
    return restored


def split_sentence_segments(text: str) -> list[tuple[str, str]]:
    """Split into sentence segments while preserving trailing whitespace (suffix)."""
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    segments: list[tuple[str, str]] = []
    pos = 0
    length = len(normalized)

    while pos < length:
        end = None
        for idx in range(pos, length):
            ch = normalized[idx]
            if ch in ".?!" and (idx + 1 == length or normalized[idx + 1].isspace()):
                end = idx + 1
                break
        if end is None:
            end = length

        sentence = normalized[pos:end]
        ws_start = end
        while end < length and normalized[end].isspace():
            end += 1
        suffix = normalized[ws_start:end]

        sentence_stripped = sentence.strip()
        # Keep empty segments (e.g., multiple newlines) as a no-op sentence so we can rebuild faithfully.
        if sentence_stripped or suffix:
            segments.append((sentence_stripped, suffix))

        pos = end

    if not segments:
        segments.append(("", ""))
    return segments


async def polish_grammar(
    *,
    raw_text: str,
    text_type: TextType,
    section_type: SectionType,
    strength: PolishStrength,
    protect_terms: bool,
    preserve_structure: bool,
) -> GrammarPolishResult:
    segments = split_sentence_segments(raw_text)
    protected_sentences: list[str] = []
    protect_maps: list[dict[str, str]] = []

    for sentence, _suffix in segments:
        if protect_terms:
            protected, mapping = protect_special_tokens(sentence)
        else:
            protected, mapping = sentence, {}
        protected_sentences.append(protected)
        protect_maps.append(mapping)

    payload = [{"index": idx, "original": sentence} for idx, sentence in enumerate(protected_sentences)]

    result = await request_chat_completion(
        messages=[
            {"role": "system", "content": build_grammar_system_prompt()},
            {
                "role": "user",
                "content": build_grammar_user_prompt(
                    sentences=payload,
                    section_type=section_type,
                    text_type=text_type,
                    strength=strength,
                    protect_terms=protect_terms,
                    preserve_structure=preserve_structure,
                ),
            },
        ],
        temperature=0.15 if strength != "deep" else 0.25,
        missing_key_message="语法校订尚未配置模型 API Key",
        failure_message="语法校订调用失败，请检查模型服务配置",
    )

    data = _extract_json_object(result.content)
    sentences = data.get("sentences")
    if not isinstance(sentences, list):
        raise BadRequest("语法校订返回 JSON 缺少 sentences 字段")
    if len(sentences) != len(segments):
        raise BadRequest("语法校订返回 sentences 数量与输入不一致")

    edits: list[SentenceEdit] = []
    revised_parts: list[str] = []

    for idx, item in enumerate(sentences):
        if not isinstance(item, dict):
            raise BadRequest("语法校订返回 sentences 项格式错误")
        if int(item.get("index", -1)) != idx:
            raise BadRequest("语法校订返回 sentences 索引不匹配")

        suffix = segments[idx][1]
        original = segments[idx][0]
        returned_original = str(item.get("original", protected_sentences[idx]))
        if returned_original != protected_sentences[idx]:
            # If the model did not preserve input, fall back to our input to keep consistency.
            returned_original = protected_sentences[idx]

        revised = str(item.get("revised", returned_original))
        edit_types = item.get("edit_types") or []
        reasons = item.get("reasons") or []
        confidence = item.get("confidence")

        if not isinstance(edit_types, list):
            edit_types = []
        if not isinstance(reasons, list):
            reasons = []

        # Restore protected tokens.
        revised = restore_special_tokens(revised, protect_maps[idx])

        changed = bool(item.get("changed", False)) and revised.strip() != original.strip()

        # Ensure placeholders or token damage didn't happen.
        if protect_terms:
            for raw in protect_maps[idx].values():
                if raw not in revised and raw in original:
                    # Do not hard-fail; preserve original instead.
                    revised = original
                    changed = False
                    edit_types = []
                    reasons = ["Protected token integrity check failed; kept original to avoid accidental changes."]
                    break

        revised_parts.append(revised + suffix)
        edits.append(
            SentenceEdit(
                index=idx,
                suffix=suffix,
                original=original,
                revised=revised,
                changed=changed,
                edit_types=[str(t) for t in edit_types if str(t).strip()],
                reasons=[str(r) for r in reasons if str(r).strip()],
                confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
            )
        )

    revised_text = "".join(revised_parts)
    return GrammarPolishResult(
        revised_text=revised_text,
        edits=edits,
        model=result.model,
        llm_tokens_used=result.total_tokens,
    )
