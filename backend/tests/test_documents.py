import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_documents_require_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/api/v1/teams/00000000-0000-0000-0000-000000000000/documents")

    response = asyncio.run(request())
    assert response.status_code == 401


def test_memory_search_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/teams/00000000-0000-0000-0000-000000000000/memory/search",
                params={"q": "decision"},
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_detail_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_hybrid_search_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/teams/00000000-0000-0000-0000-000000000000/memory/hybrid-search",
                params={"q": "decision"},
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_versions_require_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000/versions"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_text_upload_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000/upload",
                files={"file": ("notes.txt", b"hello", "text/plain")},
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_archive_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000/archive"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_download_url_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000/download-url"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_delete_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.delete(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_storage_status_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000/storage-status"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_document_version_restore_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000/versions/1/restore"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_generate_preparation_document_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(
                "/api/v1/meetings/00000000-0000-0000-0000-000000000000/"
                "preparation/generate-document"
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_publish_preparation_to_rag_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(
                "/api/v1/meetings/00000000-0000-0000-0000-000000000000/"
                "preparation/publish-to-rag",
                json={"document_id": "00000000-0000-0000-0000-000000000000"},
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_meeting_memory_search_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/meetings/00000000-0000-0000-0000-000000000000/memory/search",
                params={"q": "決策"},
            )

    response = asyncio.run(request())
    assert response.status_code == 401


def test_meeting_memory_hybrid_search_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/meetings/00000000-0000-0000-0000-000000000000/memory/hybrid-search",
                params={"q": "決策"},
            )

    response = asyncio.run(request())
    assert response.status_code == 401
