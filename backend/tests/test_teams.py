import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_teams_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/teams")

    response = asyncio.run(request())
    assert response.status_code == 401
