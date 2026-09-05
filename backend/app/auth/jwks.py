"""Short-lived public key cache; never cache a user's authentication result."""

import asyncio
from time import monotonic

import httpx

_cache: dict[str, tuple[float, list[dict]]] = {}
_lock = asyncio.Lock()


async def get_keys(url: str) -> list[dict]:
    async with _lock:
        cached = _cache.get(url)
        if cached and cached[0] > monotonic():
            return cached[1]
        async with httpx.AsyncClient(timeout=3.0) as client:
            for attempt in range(2):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    body = response.json()
                    keys = body.get("keys") if isinstance(body, dict) else None
                    if not isinstance(keys, list) or not keys or not all(
                        isinstance(key, dict) for key in keys
                    ):
                        raise httpx.HTTPError("invalid JWKS response")
                    if len(_cache) >= 4:
                        _cache.clear()
                    _cache[url] = (monotonic() + 60, keys)
                    return keys
                except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                    transient = isinstance(exc, httpx.TransportError) or (
                        exc.response.status_code >= 500
                    )
                    if attempt or not transient:
                        raise
                    await asyncio.sleep(0.2)
    raise RuntimeError("unreachable")
