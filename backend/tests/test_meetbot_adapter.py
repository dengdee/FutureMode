import asyncio

import httpx
from httpx import ASGITransport, AsyncClient

from app.api.meetbot import (
    AudioInputManager,
    _meeting_input_url,
    get_meeting_baas_client,
    join_registry,
)
from app.integrations.meetingbaas import MeetingBaasClient
from app.main import app, settings


def test_meeting_input_url_adds_scope_without_dropping_existing_query() -> None:
    assert _meeting_input_url(
        "wss://example.test/meetbot/ws/audio-in?format=pcm", "meeting-1"
    ) == "wss://example.test/meetbot/ws/audio-in?format=pcm&meeting_id=meeting-1"
    assert _meeting_input_url(None, "meeting-1") is None


def test_audio_manager_scopes_reconnections_and_cleans_up() -> None:
    async def run() -> None:
        manager = AudioInputManager()

        class Socket:
            def __init__(self) -> None:
                self.closed = False

            async def close(self, **_: object) -> None:
                self.closed = True

        first = Socket()
        second = Socket()
        await manager.connect(first, meeting_id="meeting-1")
        await manager.connect(second, meeting_id="meeting-1")
        assert first.closed is True
        await manager.disconnect(second, meeting_id="meeting-1")
        assert manager.websocket is None

    asyncio.run(run())


async def post_join(
    headers: dict[str, str] | None = None,
    *,
    meeting_id: str | None = None,
) -> httpx.Response:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            "/meetbot/join",
            json={
                "meeting_url": "https://meet.google.com/abc-defg-hij",
                **({"meeting_id": meeting_id} if meeting_id else {}),
            },
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
    monkeypatch.setattr(settings, "meeting_baas_input_url", "wss://api.example.test/audio")
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


def test_join_reports_missing_audio_input_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "meeting_baas_api_key", "test-key")
    monkeypatch.setattr(settings, "meeting_baas_input_url", None)
    response = asyncio.run(post_join({"Idempotency-Key": "missing-input-1"}))
    assert response.status_code == 201
    assert response.json()["text_card"]["reason"] == "audio_input_not_configured"


def test_join_scopes_provider_audio_url_to_meeting(monkeypatch) -> None:
    async def provider(request: httpx.Request) -> httpx.Response:
        payload = request.read()
        assert b"meeting_id=meeting-42" in payload
        return httpx.Response(201, json={"success": True, "data": {"bot_id": "bot-42"}})

    monkeypatch.setattr(settings, "meeting_baas_api_key", "test-key")
    monkeypatch.setattr(settings, "meeting_baas_input_url", "wss://api.example.test/audio")
    app.dependency_overrides[get_meeting_baas_client] = lambda: MeetingBaasClient(
        settings, transport=httpx.MockTransport(provider)
    )
    try:
        response = asyncio.run(post_join({"Idempotency-Key": "scope-42"}, meeting_id="meeting-42"))
    finally:
        app.dependency_overrides.clear()
        join_registry._responses.clear()

    assert response.status_code == 201


def test_meeting_id_scopes_idempotency_across_clients(monkeypatch) -> None:
    calls = 0

    async def provider(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(201, json={"success": True, "data": {"bot_id": "bot-shared"}})

    monkeypatch.setattr(settings, "meeting_baas_api_key", "test-key")
    monkeypatch.setattr(settings, "meeting_baas_input_url", "wss://api.example.test/audio")
    app.dependency_overrides[get_meeting_baas_client] = lambda: MeetingBaasClient(
        settings, transport=httpx.MockTransport(provider)
    )
    try:
        first = asyncio.run(post_join({"Idempotency-Key": "browser-a"}, meeting_id="meeting-shared"))
        second = asyncio.run(post_join({"Idempotency-Key": "browser-b"}, meeting_id="meeting-shared"))
    finally:
        app.dependency_overrides.clear()
        join_registry._responses.clear()

    assert first.json()["bot_id"] == "bot-shared"
    assert second.json()["bot_id"] == "bot-shared"
    assert calls == 1
