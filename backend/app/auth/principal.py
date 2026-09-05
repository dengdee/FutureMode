"""JWT verification and authenticated principal dependency."""

import logging
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, WebSocket

from app.config import Settings, get_settings

logger = logging.getLogger("proximate.auth")


@dataclass(frozen=True)
class Principal:
    subject: str
    claims: dict[str, Any]


async def get_current_principal(
    request: Request, settings: Settings = Depends(get_settings)
) -> Principal:
    authorization = request.headers.get("Authorization", "")
    cookie_header = request.headers.get("Cookie", "")
    if not authorization:
        token = _session_cookie_token(cookie_header)
        if token:
            authorization = f"Bearer {token}"
    return await principal_from_authorization(authorization, settings, cookie_header=cookie_header)


async def get_websocket_principal(
    websocket: WebSocket, settings: Settings = Depends(get_settings)
) -> Principal:
    authorization = websocket.headers.get("Authorization", "")
    cookie_header = websocket.headers.get("Cookie", "")
    if not authorization:
        token = _session_cookie_token(cookie_header)
        if token:
            authorization = f"Bearer {token}"
    return await principal_from_authorization(authorization, settings, cookie_header=cookie_header)


def _session_cookie_token(cookie_header: str) -> str | None:
    """Read either Neon Auth cookie name without exposing its value in logs."""
    if not cookie_header:
        return None
    cookies = SimpleCookie()
    cookies.load(cookie_header)
    for name in ("__Secure-neon-auth.session_token", "neon-auth.session_token"):
        value = cookies.get(name)
        if value and value.value.strip():
            return value.value.strip()
    return None


async def principal_from_authorization(
    authorization: str, settings: Settings, cookie_header: str = ""
) -> Principal:
    """Verify a bearer token shared by HTTP and WebSocket authentication."""
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
            logger.info("authorization_present=true token_type=opaque")
            session_url = settings.neon_auth_session_url or (
                f"{settings.neon_auth_base_url.rstrip('/')}/api/auth/get-session"
                if settings.neon_auth_base_url
                else None
            )
            if not session_url:
                raise ValueError("session endpoint is not configured")
            async with httpx.AsyncClient(timeout=5.0) as client:
                session_cookie = cookie_header or (
                    f"__Secure-neon-auth.session_token={token}; "
                    f"neon-auth.session_token={token}"
                )
                response = await client.get(session_url, headers={"Cookie": session_cookie})
                response.raise_for_status()
            logger.info("session_request_status=%s", response.status_code)
            body = response.json()
            if isinstance(body, dict) and isinstance(body.get("data"), dict):
                body = body["data"]
            user = body.get("user") if isinstance(body, dict) else None
            logger.info(
                "response_keys=%s user_exists=%s",
                ",".join(body.keys()) if isinstance(body, dict) else "",
                isinstance(user, dict),
            )
            subject = user.get("id") if isinstance(user, dict) else None
            if not isinstance(subject, str) or not subject:
                raise ValueError("session user is missing")
            logger.info("user_id_exists=true principal_created=true")
            claims = {"sub": subject, "session": True}
            return Principal(subject=subject, claims=claims)
        header = jwt.get_unverified_header(token)
        logger.info("authorization_present=true token_type=jwt")
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
