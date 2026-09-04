import httpx

from app.config import Settings


class EmbeddingConfigurationError(RuntimeError):
    pass


async def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
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
