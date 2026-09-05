"""JWT verification and authenticated principal dependency."""

from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, Request

from app.config import Settings, get_settings


@dataclass(frozen=True)
class Principal:
    subject: str
    claims: dict[str, Any]


async def get_current_principal(
    request: Request, settings: Settings = Depends(get_settings)
) -> Principal:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    if not settings.neon_auth_configured:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        # Neon Auth browser sessions commonly use an opaque cookie token.
        if token.count(".") != 2:
            session_url = settings.neon_auth_session_url or (
                f"{settings.neon_auth_base_url.rstrip('/')}/api/auth/get-session"
                if settings.neon_auth_base_url
                else None
            )
            if not session_url:
                raise ValueError("session endpoint is not configured")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    session_url,
                    headers={"Cookie": f"__Secure-neon-auth.session_token={token}"},
                )
                response.raise_for_status()
            body = response.json()
            user = body.get("user") if isinstance(body, dict) else None
            subject = user.get("id") if isinstance(user, dict) else None
            if not isinstance(subject, str) or not subject:
                raise ValueError("session user is missing")
            claims = {"sub": subject, "session": True}
            return Principal(subject=subject, claims=claims)
        header = jwt.get_unverified_header(token)
        key_id = header.get("kid")
        if not key_id or header.get("alg") != "RS256":
            raise ValueError("unsupported token header")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.neon_auth_jwks_url)
            response.raise_for_status()
        key = next(
            (item for item in response.json().get("keys", []) if item.get("kid") == key_id), None
        )
        if key is None:
            raise ValueError("signing key not found")
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=settings.neon_auth_issuer,
            audience=settings.neon_auth_audience,
        )
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("subject is missing")
    except (httpx.HTTPError, jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="invalid bearer token") from None
    return Principal(subject=subject, claims=claims)
