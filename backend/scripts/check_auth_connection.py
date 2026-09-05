"""Read-only authentication connectivity checks; never prints keys or session contents."""

import asyncio
from time import monotonic
from urllib.parse import urlsplit

import httpx

from app.config import Settings


async def main():
    settings = Settings()
    targets = {
        "backend health": "http://localhost:8000/health",
        "frontend token (no login)": "http://localhost:3000/api/auth/token",
        "Neon JWKS": settings.neon_auth_jwks_url,
        "Neon session (no login)": settings.neon_auth_session_url,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        for label, url in targets.items():
            if not url:
                print(label, "not configured")
                continue
            started = monotonic()
            try:
                response = await client.get(url)
                print(label, "host=" + str(urlsplit(url).hostname),
                      "http=" + str(response.status_code),
                      "seconds=" + str(round(monotonic() - started, 2)))
            except httpx.HTTPError as exc:
                print(label, type(exc).__name__,
                      "seconds=" + str(round(monotonic() - started, 2)))


if __name__ == "__main__":
    asyncio.run(main())
