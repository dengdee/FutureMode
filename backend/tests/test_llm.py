import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.config import Settings
from app.services.llm import LLMConfigurationError, complete_preparation


def test_groq_completion_uses_free_provider():
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(
        200, json={"choices": [{"message": {"content": "整理後的重點"}}]}, request=request
    )
    with patch(
        "app.services.llm.httpx.AsyncClient.post", new=AsyncMock(return_value=response)
    ) as post:
        result = asyncio.run(
            complete_preparation(
                [{"role": "user", "content": "議題"}],
                Settings(_env_file=None, groq_api_key="test"),
            )
        )
    assert result == "整理後的重點"
    assert post.call_args.args[0].startswith("https://api.groq.com/")


def test_completion_without_key_is_clear_error():
    with pytest.raises(LLMConfigurationError):
        asyncio.run(complete_preparation([], Settings(_env_file=None)))
