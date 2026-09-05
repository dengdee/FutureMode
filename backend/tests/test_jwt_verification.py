"""Exercise real signatures through the principal verifier, with a mocked JWKS server."""

import asyncio
import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from fastapi import HTTPException

from app.auth.principal import principal_from_authorization
from app.config import Settings


@pytest.fixture(params=["RS256", "ES256", "EdDSA"])
def signing(request, monkeypatch):
    algorithm = request.param
    keys = {
        "RS256": lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048),
        "ES256": lambda: ec.generate_private_key(ec.SECP256R1()),
        "EdDSA": ed25519.Ed25519PrivateKey.generate,
    }
    key = keys[algorithm]()
    public = json.loads(jwt.get_algorithm_by_name(algorithm).to_jwk(key.public_key()))
    public.update(kid="test-key", alg=algorithm)

    async def get(self, url, **kwargs):
        assert url == "https://auth.example/jwks"
        return httpx.Response(200, json={"keys": [public]}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    settings = Settings(
        _env_file=None,
        neon_auth_base_url="https://auth.example",
        neon_auth_issuer="https://auth.example",
        neon_auth_audience="your-neon-auth-audience",
        neon_auth_jwks_url="https://auth.example/jwks",
    )

    def verify(*, tamper=False, **overrides):
        claims = dict(sub="test-user", iss="https://auth.example", aud="https://auth.example",
                      exp=int(time.time()) + 60)
        claims.update(overrides)
        token = jwt.encode(claims, key, algorithm=algorithm, headers={"kid": "test-key"})
        if tamper:
            header, payload, signature = token.split(".")
            signature = ("A" if signature[0] != "A" else "B") + signature[1:]
            token = ".".join((header, payload, signature))
        return asyncio.run(principal_from_authorization(f"Bearer {token}", settings))

    return verify


def test_valid_signature_creates_principal(signing):
    assert signing().subject == "test-user"


def test_modified_signature_rejected(signing):
    with pytest.raises(HTTPException) as exc:
        signing(tamper=True)
    assert exc.value.status_code == 401


@pytest.mark.parametrize("claims", [
    {"aud": "another-app"}, {"iss": "https://attacker.example"}, {"exp": 1}, {"sub": ""},
])
def test_invalid_claims_rejected(signing, claims):
    with pytest.raises(HTTPException) as exc:
        signing(**claims)
    assert exc.value.status_code == 401


def test_session_forwards_only_auth_cookies(monkeypatch):
    async def get(self, url, **kwargs):
        assert url == "https://auth.example/get-session"
        assert "unrelated" not in kwargs["headers"]["Cookie"]
        assert "session_token=signed-session" in kwargs["headers"]["Cookie"]
        return httpx.Response(200, json={"user": {"id": "user"}},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    settings = Settings(_env_file=None, neon_auth_base_url="https://auth.example")
    result = asyncio.run(principal_from_authorization(
        "Bearer opaque", settings,
        cookie_header="unrelated=private; neon-auth.session_token=signed-session",
    ))
    assert result.subject == "user"
