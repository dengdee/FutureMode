"""Small, mockable boundary around the Meeting BaaS Bot API."""

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from app.config import Settings


class MeetingBaasError(Exception):
    """A provider failure expressed without provider response details."""

    def __init__(self, *, status_code: int = 502, code: str = "meeting_baas_unavailable") -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code


class MeetingBaasConfigurationError(MeetingBaasError):
    def __init__(self) -> None:
        super().__init__(status_code=503, code="meeting_baas_not_configured")


class MeetingBaasClient:
    """HTTP client with bounded retries for failures that are safe to retry."""

    def __init__(
        self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.settings = settings
        self._transport = transport

    @property
    def _headers(self) -> dict[str, str]:
        if not self.settings.meeting_baas_api_key:
            raise MeetingBaasConfigurationError()
        return {"x-meeting-baas-api-key": self.settings.meeting_baas_api_key}

    async def create_bot(
        self, payload: Mapping[str, Any], *, idempotency_key: str
    ) -> dict[str, Any]:
        retries = max(0, self.settings.meeting_baas_max_retries)
        headers = {**self._headers, "Idempotency-Key": idempotency_key}
        timeout = httpx.Timeout(self.settings.meeting_baas_timeout_seconds)
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, transport=self._transport) as client:
                    response = await client.post(
                        self.settings.meeting_baas_url,
                        headers=headers,
                        json=dict(payload),
                    )
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise MeetingBaasError() from None
            if response.status_code >= 500 or response.status_code == 429:
                if attempt < retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise MeetingBaasError(status_code=503, code="meeting_baas_unavailable")
            if response.is_error:
                raise MeetingBaasError(status_code=502, code="meeting_baas_request_rejected")
            try:
                body = response.json()
            except ValueError:
                raise MeetingBaasError(code="meeting_baas_invalid_response") from None
            if not isinstance(body, dict):
                raise MeetingBaasError(code="meeting_baas_invalid_response")
            if body.get("success") is False:
                raise MeetingBaasError(status_code=502, code="meeting_baas_request_rejected")
            return body
        raise AssertionError("unreachable")

    async def get_bot(self, bot_id: str) -> dict[str, Any]:
        return await self._request("GET", f"{self.settings.meeting_baas_url}/{bot_id}")

    async def leave_bot(self, bot_id: str) -> dict[str, Any]:
        return await self._request(
            "POST", f"{self.settings.meeting_baas_url}/{bot_id}/leave", json={}
        )

    async def _request(
        self, method: str, url: str, *, json: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.meeting_baas_timeout_seconds),
                transport=self._transport,
            ) as client:
                response = await client.request(method, url, headers=self._headers, json=json)
        except (httpx.TimeoutException, httpx.NetworkError):
            raise MeetingBaasError() from None
        if response.is_error:
            raise MeetingBaasError(status_code=502, code="meeting_baas_request_rejected")
        if not response.content:
            return {}
        try:
            body = response.json()
        except ValueError:
            raise MeetingBaasError(code="meeting_baas_invalid_response") from None
        if not isinstance(body, dict):
            raise MeetingBaasError(code="meeting_baas_invalid_response")
        if body.get("success") is False:
            raise MeetingBaasError(status_code=502, code="meeting_baas_request_rejected")
        return body
