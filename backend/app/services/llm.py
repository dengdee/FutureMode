"""Small provider adapter for pre-meeting conversation."""

import httpx

from app.config import Settings


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


async def complete_preparation(messages: list[dict[str, str]], settings: Settings) -> str:
    if settings.llm_provider == "gemini":
        return await _complete_gemini(messages, settings)
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


async def generate_preparation_document(
    messages: list[dict[str, str]], settings: Settings
) -> str:
    """Turn a private preparation chat into a meeting-ready Markdown brief."""
    instruction = {
        "role": "user",
        "content": (
            "請將以上議前對話整理成可供會議中檢索的繁體中文 Markdown 文件。"
            "請包含：背景與目標、已確認的事實、待決問題、不同觀點、風險與限制、"
            "建議的會議討論順序，以及明確的待辦事項。只整理對話中出現的資訊；"
            "不確定的內容請標記為待確認，不要捏造。"
        ),
    }
    return await complete_preparation([*messages, instruction], settings)
async def _complete_gemini(messages: list[dict[str, str]], settings: Settings) -> str:
    api_key = settings.gemini_api_key or settings.llm_api_key
    if not api_key:
        raise LLMConfigurationError("Gemini provider is not configured")
    contents = [
        {"role": "model" if item["role"] == "assistant" else "user",
         "parts": [{"text": item["content"]}]}
        for item in messages
    ]
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.llm_model}:generateContent"
        )
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                url,
                params={"key": api_key},
                json={
                    "systemInstruction": {"parts": [{"text": (
                        "你是會議前準備助理。請用繁體中文協助使用者釐清問題、風險與需要在會議"
                        "決定的事項；不要假造外部事實。"
                    )}]},
                    "contents": contents,
                    "generationConfig": {"temperature": 0.3},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            if not isinstance(content, str) or not content.strip():
                raise LLMProviderError("LLM returned empty content")
            return content.strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("Gemini provider unavailable") from exc
