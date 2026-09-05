"""Account invitations require a signed identity, not email claims or a session cookie."""
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi import FastAPI

from app.api.teams import database_session, router
from app.auth import principal as auth
from app.config import Settings, get_settings


@pytest.mark.parametrize("expired,expected", [(False, 200), (True, 401)])
def test_actual_inbox_accepts_sparse_jwt_without_cookie(monkeypatch, expired, expected):
    key = ed25519.Ed25519PrivateKey.generate()
    public = json.loads(jwt.get_algorithm_by_name("EdDSA").to_jwk(key.public_key()))
    public.update(kid="test", alg="EdDSA")
    monkeypatch.setattr(auth, "get_keys", AsyncMock(return_value=[public]))
    settings = Settings(_env_file=None, neon_auth_base_url="https://auth.example",
                        neon_auth_issuer="https://auth.example", neon_auth_audience="app",
                        neon_auth_jwks_url="https://auth.example/jwks")
    db = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    async def database():
        yield db

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[database_session] = database
    token = jwt.encode({"sub": "account-a", "iss": "https://auth.example", "aud": "app",
                        "exp": 1 if expired else int(time.time()) + 60}, key,
                       algorithm="EdDSA", headers={"kid": "test"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as client:
            return await client.get("/api/v1/me/invitations", headers={
                "Authorization": f"Bearer {token}", "X-Email": "attacker@example.com",
            })

    response = asyncio.run(run())
    assert response.status_code == expected
    if expected == 200:
        assert response.json() == []
    else:
        db.execute.assert_not_awaited()
