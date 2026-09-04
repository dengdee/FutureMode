import httpx

from app.config import Settings


class SpeechConfigurationError(RuntimeError):
    pass


async def transcribe_audio(
    filename: str, content: bytes, content_type: str, settings: Settings
) -> str:
    if not settings.groq_api_key:
        raise SpeechConfigurationError("Groq STT provider is not configured")
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": (filename, content, content_type)},
            data={"model": settings.groq_stt_model, "response_format": "json"},
        )
    response.raise_for_status()
    return response.json()["text"]
