"""Small provider adapter for pre-meeting conversation."""

import httpx

from app.config import Settings


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


async def complete_preparation(messages: list[dict[str, str]], settings: Settings) -> str:
    api_key = settings.llm_api_key or settings.groq_api_key
    if settings.llm_provider not in {"groq", "openai"} or not api_key:
        raise LLMConfigurationError("LLM provider is not configured")
    system = {
        "role": "system",
        "content": (
            "你是會議前準備助理。請用繁體中文協助使用者釐清問題、風險與需要在會議"
            "決定的事項；不要假造外部事實。"
        ),
    }
    try:
        base_url = (
            "https://api.groq.com/openai/v1/chat/completions"
            if settings.llm_provider == "groq"
            else "https://api.openai.com/v1/chat/completions"
        )
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                base_url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": settings.llm_model,
                    "messages": [system, *messages],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise LLMProviderError("LLM returned empty content")
            return content.strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("LLM provider unavailable") from exc
