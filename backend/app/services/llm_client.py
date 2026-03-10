"""Shared client for chat-style LLM completions."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import httpx

from app.core.config import get_settings
from app.core.exceptions import BadRequest


logger = logging.getLogger(__name__)


@dataclass
class ChatCompletionResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


async def request_chat_completion(
    *,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    missing_key_message: str,
    failure_message: str,
) -> ChatCompletionResult:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.LLM_API_KEY.strip():
        logger.warning(
            "LLM API key is empty at runtime",
            extra={
                "llm_api_base_url": settings.LLM_API_BASE_URL,
                "llm_model": settings.LLM_MODEL,
            },
        )
        raise BadRequest(missing_key_message)

    url = f"{settings.LLM_API_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.LLM_MODEL,
        "temperature": temperature,
        "messages": messages,
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
        detail = failure_message
        try:
            error_payload = exc.response.json()
            message = error_payload.get("error", {}).get("message")
            if isinstance(message, str) and message.strip():
                detail = f"{failure_message}: {message.strip()}"
        except ValueError:
            pass
        raise BadRequest(detail) from exc
    except httpx.HTTPError as exc:
        raise BadRequest(failure_message) from exc

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))

    normalized_content = str(content).strip()
    if not normalized_content:
        raise BadRequest("大模型未返回有效内容")

    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))

    return ChatCompletionResult(
        content=normalized_content,
        model=str(data.get("model") or settings.LLM_MODEL),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
