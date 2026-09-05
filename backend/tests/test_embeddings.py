import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.config import Settings
from app.services.embeddings import EmbeddingConfigurationError, embed_texts


def test_gemini_embeddings_use_configured_pgvector_dimension() -> None:
    request = httpx.Request(
        "POST",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent",
    )
    response = httpx.Response(
        200,
        json={"embedding": {"values": [0.1, 0.2]}},
        request=request,
    )
    settings = Settings(
        _env_file=None,
        embedding_provider="gemini",
        embedding_model="gemini-embedding-001",
        embedding_dimensions=2,
        gemini_api_key="test-key",
    )
    with patch(
        "app.services.embeddings.httpx.AsyncClient.post",
        new=AsyncMock(return_value=response),
    ) as post:
        result = asyncio.run(embed_texts(["議前重點"], settings))

    assert result == [[0.1, 0.2]]
    assert post.call_args.kwargs["json"]["outputDimensionality"] == 2


def test_gemini_embeddings_without_key_are_clear() -> None:
    with pytest.raises(EmbeddingConfigurationError):
        asyncio.run(
            embed_texts(
                ["議前重點"],
                Settings(_env_file=None, embedding_provider="gemini"),
            )
        )
