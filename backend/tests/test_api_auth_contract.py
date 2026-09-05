"""Contract checks for the authentication boundary of every versioned API route."""

import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app

_UUID = "00000000-0000-0000-0000-000000000000"


def _concrete_path(path: str) -> str:
    return (
        path.replace("{meeting_id}", _UUID)
        .replace("{team_id}", _UUID)
        .replace("{document_id}", _UUID)
        .replace("{version_id}", _UUID)
        .replace("{item_id}", _UUID)
        .replace("{user_id}", _UUID)
        .replace("{suggestion_id}", _UUID)
        .replace("{invitation_id}", _UUID)
        .replace("{bot_id}", "test-bot")
        .replace("{version}", "1")
    )


def _protected_operations() -> list[tuple[str, str]]:
    operations: list[tuple[str, str]] = []
    for path, methods in app.openapi()["paths"].items():
        if not path.startswith("/api/v1/") or path == "/api/v1/auth/config":
            continue
        # Meeting BaaS calls this webhook with its own shared secret.
        if path == "/api/v1/meetings/{meeting_id}/transcripts/backup":
            continue
        for method in methods:
            if method in {"get", "post", "patch", "put", "delete"}:
                operations.append((method.upper(), _concrete_path(path)))
    return operations


def test_every_versioned_api_operation_requires_authentication() -> None:
    async def request_all() -> list[tuple[str, str, int]]:
        results = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for method, path in _protected_operations():
                response = await client.request(method, path)
                results.append((method, path, response.status_code))
        return results

    results = asyncio.run(request_all())

    assert len(results) >= 40
    failures = [result for result in results if result[2] != 401]
    assert failures == []


def test_openapi_exposes_all_expected_api_groups() -> None:
    paths = set(app.openapi()["paths"])

    for path in (
        "/api/v1/me",
        "/api/v1/teams",
        "/api/v1/meetings",
        "/api/v1/meetings/{meeting_id}/agenda",
        "/api/v1/meetings/{meeting_id}/transcripts",
        "/api/v1/teams/{team_id}/memory/hybrid-search",
        "/meetbot/join",
    ):
        assert path in paths
