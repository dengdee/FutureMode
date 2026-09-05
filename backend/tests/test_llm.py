import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.config import Settings
from app.services.llm import LLMConfigurationError, complete_preparation, generate_meeting_speech


def test_gemini_completion_uses_free_provider():
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent")
    response = httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": "整理後的重點"}]}}]},
        request=request,
    )
    with patch(
        "app.services.llm.httpx.AsyncClient.post", new=AsyncMock(return_value=response)
    ) as post:
        result = asyncio.run(
            complete_preparation(
                [{"role": "user", "content": "議題"}],
                Settings(_env_file=None, gemini_api_key="test"),
            )
        )
    assert result == "整理後的重點"
    assert post.call_args.args[0].startswith("https://generativelanguage.googleapis.com/")


def test_completion_without_key_is_clear_error():
    with pytest.raises(LLMConfigurationError):
        asyncio.run(complete_preparation([], Settings(_env_file=None)))


def test_meeting_speech_prompt_is_short_and_speakable():
    request = httpx.Request(
        "POST",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
    )
    response = httpx.Response(
        200,
        json={
            "candidates": [
                {"content": {"parts": [{"text": "我建議先確認上線風險，再決定回滾方案。"}]}}
            ]
        },
        request=request,
    )
    with patch(
        "app.services.llm.httpx.AsyncClient.post", new=AsyncMock(return_value=response)
    ) as post:
        result = asyncio.run(
            generate_meeting_speech(
                "提出上線風險",
                "目前討論版本發布時程",
                Settings(_env_file=None, gemini_api_key="test"),
            )
        )
    assert result.startswith("我建議")
    body = post.call_args.kwargs["json"]
    assert "提出上線風險" in body["contents"][0]["parts"][0]["text"]
    assert "目前討論版本發布時程" in body["contents"][0]["parts"][0]["text"]
