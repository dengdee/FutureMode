import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app, settings


async def request_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health")


async def request(path: str, **kwargs):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request("GET", path, **kwargs)


def test_health() -> None:
    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "development"}
    assert response.headers["x-request-id"]


def test_ready_reports_unconfigured_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    response = asyncio.run(request("/ready"))

    assert response.status_code == 200
    assert response.json()["checks"]["database"] == "not_configured"


def test_ready_includes_request_id() -> None:
    response = asyncio.run(request("/ready"))

    assert response.headers["x-request-id"]


def test_validation_error_is_sanitized() -> None:
    transport = ASGITransport(app=app)

    async def send_request():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/meetbot/join", json={"meeting_url": "not-a-url"})

    response = asyncio.run(send_request())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "not-a-url" not in response.text
