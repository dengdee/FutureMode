import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_me_requires_bearer_token() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/me")

    response = asyncio.run(request())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "http_error"


def test_me_rejects_malformed_token(monkeypatch) -> None:
    from app.main import settings

    monkeypatch.setattr(settings, "neon_auth_issuer", "https://issuer.example")
    monkeypatch.setattr(settings, "neon_auth_audience", "audience")
    monkeypatch.setattr(settings, "neon_auth_jwks_url", "https://issuer.example/jwks")

    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"})

    response = asyncio.run(request())
    assert response.status_code == 401
