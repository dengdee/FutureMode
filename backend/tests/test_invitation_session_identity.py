import asyncio
import json
import time
from unittest.mock import AsyncMock

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi import Depends, FastAPI

from app.api.teams import invitation_email
from app.auth import principal as auth
from app.config import Settings, get_settings


@pytest.fixture
def client_case(monkeypatch):
    key = ed25519.Ed25519PrivateKey.generate()
    public = json.loads(jwt.get_algorithm_by_name("EdDSA").to_jwk(key.public_key()))
    public.update(kid="test", alg="EdDSA")
    monkeypatch.setattr(auth, "get_keys", AsyncMock(return_value=[public]))
    settings = Settings(_env_file=None, neon_auth_base_url="https://auth.example",
                        neon_auth_issuer="https://auth.example",
                        neon_auth_audience="app", neon_auth_jwks_url="https://auth.example/jwks",
                        neon_auth_session_url="https://auth.example/auth/get-session")
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings

    @app.get("/api/v1/me/invitations")
    async def inbox(principal=Depends(auth.get_current_principal)):
        return {"email": invitation_email(principal), "subject": principal.subject}

    user = {"id": "recipient", "email": "person@example.com", "emailVerified": True}
    calls = []

    async def send(body=None, cookie=True, expired=False, status=200):
        token = jwt.encode({"sub": "recipient", "iss": "https://auth.example", "aud": "app",
                            "exp": 1 if expired else int(time.time()) + 60}, key,
                           algorithm="EdDSA", headers={"kid": "test"})
        original_get = httpx.AsyncClient.get

        async def upstream(client, url, **kwargs):
            if url == "/api/v1/me/invitations":
                return await original_get(client, url, **kwargs)
            calls.append((url, kwargs))
            assert url == settings.neon_auth_session_url
            assert "unrelated" not in kwargs["headers"]["Cookie"]
            return httpx.Response(status, json=body if body is not None else {
                "session": {"userId": "recipient"}, "user": user,
            }, request=httpx.Request("GET", url))

        monkeypatch.setattr(httpx.AsyncClient, "get", upstream)
        headers = {"Authorization": f"Bearer {token}", "X-Email": "attacker@example.com"}
        if cookie:
            headers["Cookie"] = "neon-auth.session_token=test-session; unrelated=private"
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as client:
            return await client.get("/api/v1/me/invitations", headers=headers)

    return send, calls, user


def test_sparse_signed_jwt_uses_same_account_verified_session(client_case):
    send, calls, _ = client_case
    response = asyncio.run(send())
    assert response.status_code == 200
    assert response.json() == {"subject": "recipient", "email": "person@example.com"}
    assert len(calls) == 1


def test_nested_neon_session_supported(client_case):
    send, _, user = client_case
    response = asyncio.run(send(body={"data": {"session": {"userId": "recipient"},
                                               "user": user}}))
    assert response.status_code == 200


@pytest.mark.parametrize("body", [
    {"session": {"userId": "other"}, "user": {"id": "other"}},
    {"session": None, "user": {"id": "recipient"}},
    {"session": {"userId": "other"}, "user": {"id": "recipient"}},
])
def test_missing_or_different_session_rejected(client_case, body):
    send, _, _ = client_case
    assert asyncio.run(send(body=body)).status_code == 401


def test_unverified_session_cannot_redeem(client_case):
    send, _, user = client_case
    user["emailVerified"] = False
    assert asyncio.run(send()).status_code == 403


def test_missing_cookie_never_trusts_client_email(client_case):
    send, calls, _ = client_case
    assert asyncio.run(send(cookie=False)).status_code == 403
    assert not calls


def test_expired_jwt_rejected_before_cookie_lookup(client_case):
    send, calls, _ = client_case
    assert asyncio.run(send(expired=True)).status_code == 401
    assert not calls


def test_upstream_failure_returns_retryable_error(client_case):
    send, _, _ = client_case
    assert asyncio.run(send(status=500)).status_code == 503
