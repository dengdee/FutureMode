import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_auth_config_does_not_expose_secrets() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/auth/config")

    response = asyncio.run(request())
    assert response.status_code == 200
    assert "jwks_url" not in response.json()
    assert "client_secret" not in response.json()
