import asyncio

import httpx
from httpx import ASGITransport, AsyncClient

from app.api.meetbot import get_meeting_baas_client, join_registry
from app.integrations.meetingbaas import MeetingBaasClient
from app.main import app, settings


async def post_join(headers: dict[str, str] | None = None) -> httpx.Response:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            "/meetbot/join",
            json={"meeting_url": "https://meet.google.com/abc-defg-hij"},
            headers=headers,
        )


def test_join_uses_stable_schema_and_does_not_create_duplicate_bot(monkeypatch) -> None:
    calls = 0

    async def provider(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.headers["Idempotency-Key"] == "join-1"
        return httpx.Response(
            201,
            json={"success": True, "data": {"bot_id": "bot-123"}},
        )

    monkeypatch.setattr(settings, "meeting_baas_api_key", "test-key")
    app.dependency_overrides[get_meeting_baas_client] = lambda: MeetingBaasClient(
        settings, transport=httpx.MockTransport(provider)
    )
    try:
        first = asyncio.run(post_join({"Idempotency-Key": "join-1"}))
        second = asyncio.run(post_join({"Idempotency-Key": "join-1"}))
    finally:
        app.dependency_overrides.clear()
        join_registry._responses.clear()

    assert first.status_code == 201
    assert first.json() == {
        "bot_id": "bot-123",
        "status": "pending",
        "idempotency_key": "join-1",
        "text_card": None,
    }
    assert second.status_code == 201
    assert calls == 1


def test_provider_failure_falls_back_to_text_card_without_provider_detail(monkeypatch) -> None:
    async def provider(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="secret provider detail")

    monkeypatch.setattr(settings, "meeting_baas_api_key", "test-key")
    monkeypatch.setattr(settings, "meeting_baas_max_retries", 0)
    app.dependency_overrides[get_meeting_baas_client] = lambda: MeetingBaasClient(
        settings, transport=httpx.MockTransport(provider)
    )
    try:
        response = asyncio.run(post_join({"Idempotency-Key": "failure-1"}))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["status"] == "text_card"
    assert response.json()["text_card"]["reason"] == "voice_bot_unavailable"
    assert "secret provider detail" not in response.text
