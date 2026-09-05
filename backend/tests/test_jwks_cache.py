import asyncio

import httpx
import pytest

from app.auth import jwks


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(jwks, "_cache", {})
    monkeypatch.setattr(jwks, "_lock", asyncio.Lock())


def test_concurrent_requests_fetch_once(monkeypatch):
    calls = []

    async def get(self, url):
        calls.append(url)
        await asyncio.sleep(0)
        return httpx.Response(
            200, json={"keys": [{"kid": "key"}]}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    async def run():
        results = await asyncio.gather(
            *(jwks.get_keys("https://auth.example/jwks") for _ in range(4))
        )
        assert all(result == [{"kid": "key"}] for result in results)

    asyncio.run(run())
    assert len(calls) == 1


def test_transient_failure_retried_and_cached(monkeypatch):
    calls = []

    async def get(self, url):
        calls.append(url)
        if len(calls) == 1:
            raise httpx.ConnectError("connection reset")
        return httpx.Response(
            200, json={"keys": [{"kid": "key"}]}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    async def run():
        await jwks.get_keys("https://auth.example/jwks")
        await jwks.get_keys("https://auth.example/jwks")

    asyncio.run(run())
    assert len(calls) == 2


def test_expired_cache_not_used_on_outage(monkeypatch):
    url = "https://auth.example/jwks"
    jwks._cache[url] = (0, [{"kid": "old"}])
    calls = []

    async def get(self, url):
        calls.append(url)
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    with pytest.raises(httpx.ConnectError):
        asyncio.run(jwks.get_keys(url))
    assert len(calls) == 2
