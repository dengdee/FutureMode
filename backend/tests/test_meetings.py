import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_meetings_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/meetings")

    response = asyncio.run(request())
    assert response.status_code == 401


def test_meeting_detail_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/meetings/00000000-0000-0000-0000-000000000000")

    response = asyncio.run(request())
    assert response.status_code == 401
