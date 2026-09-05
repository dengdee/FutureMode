import httpx

from app.config import Settings


class EmbeddingConfigurationError(RuntimeError):
    pass


async def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
    if settings.embedding_provider == "gemini":
        return await _embed_with_gemini(texts, settings)
    if settings.embedding_provider != "openai":
        raise EmbeddingConfigurationError("unsupported embedding provider")
    if not settings.embedding_api_key:
        raise EmbeddingConfigurationError("embedding provider is not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
            json={"model": settings.embedding_model, "input": texts},
        )
    response.raise_for_status()
    data = response.json()["data"]
    return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]


async def _embed_with_gemini(texts: list[str], settings: Settings) -> list[list[float]]:
    """Use Gemini's free embedding endpoint with the pgvector column dimension."""
    api_key = settings.gemini_api_key or settings.llm_api_key or settings.embedding_api_key
    if not api_key:
        raise EmbeddingConfigurationError("Gemini embedding provider is not configured")
    vectors: list[list[float]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for text in texts:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{settings.embedding_model}:embedContent",
                params={"key": api_key},
                json={
                    "model": f"models/{settings.embedding_model}",
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": settings.embedding_dimensions,
                },
            )
            response.raise_for_status()
            values = response.json()["embedding"]["values"]
            if not isinstance(values, list) or len(values) != settings.embedding_dimensions:
                raise EmbeddingConfigurationError("Gemini returned an invalid embedding")
            vectors.append(values)
    return vectors
