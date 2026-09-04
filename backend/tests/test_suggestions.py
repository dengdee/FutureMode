import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_suggestions_require_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/meetings/00000000-0000-0000-0000-000000000000/suggestions"
            )

    response = asyncio.run(request())
    assert response.status_code == 401
