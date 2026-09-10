"""Compatibility routes for the Meeting BaaS voice-bot integration."""

import tempfile
import wave
from pathlib import Path
import asyncio
import hashlib
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, get_settings
from app.db.session import get_session
from app.integrations.meetingbaas import (
    MeetingBaasClient,
    MeetingBaasError,
)
from app.models import BotSession, Transcript
import edge_tts
import miniaudio
import httpx
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

settings = get_settings()

router = APIRouter(
    prefix="/meetbot",
    tags=["meetbot"],
)


# ============================================================
# Models
# ============================================================


class JoinMeetingRequest(BaseModel):
    meeting_url: HttpUrl
    meeting_id: str | None = Field(default=None, min_length=1, max_length=64)


class TextCardFallback(BaseModel):
    available: bool = True
    reason: str


class JoinMeetingResponse(BaseModel):
    bot_id: str | None = None
    status: str = Field(description="pending or text_card")
    idempotency_key: str
    text_card: TextCardFallback | None = None


class BotStatusResponse(BaseModel):
    bot_id: str
    status: str


class LeaveMeetingResponse(BaseModel):
    bot_id: str
    status: str = "leaving"


class SpeakRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )
    meeting_id: str | None = Field(default=None, min_length=1, max_length=64)


# ============================================================
# Join Registry
# ============================================================


class _JoinRegistry:
    """
    Process-local idempotency cache.

    Suitable for the current single-bot PoC.
    """

    def __init__(self) -> None:
        self._responses: dict[str, JoinMeetingResponse] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        key: str,
        create: Callable[[], Awaitable[JoinMeetingResponse]],
    ) -> JoinMeetingResponse:

        async with self._lock:
            existing = self._responses.get(key)

            if existing:
                return existing

            response = await create()

            if response.bot_id:
                self._responses[key] = response

            return response


join_registry = _JoinRegistry()


# ============================================================
# Dependencies
# ============================================================


def get_meeting_baas_client(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[MeetingBaasClient]:

    yield MeetingBaasClient(settings)


# ============================================================
# Helpers
# ============================================================


def _idempotency_key(
    meeting_url: HttpUrl,
    supplied_key: str | None,
    meeting_id: str | None = None,
) -> str:

    # A meeting has one shared Bot. Ignore per-browser idempotency keys when
    # the caller supplies the persisted meeting id, so different participants
    # cannot create duplicate provider bots by clicking at the same time.
    if meeting_id and meeting_id.strip():
        return f"meeting:{meeting_id.strip()}"
    if supplied_key and supplied_key.strip():
        return supplied_key.strip()

    scope = f"{meeting_url}|{meeting_id or ''}"
    return hashlib.sha256(scope.encode()).hexdigest()

def _meeting_input_url(base_url: str | None, meeting_id: str | None) -> str | None:
    """Attach an optional meeting scope without breaking existing provider URLs."""
    if not base_url or not meeting_id:
        return base_url
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["meeting_id"] = meeting_id
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

def _provider_data(
    response: dict[str, Any],
) -> dict[str, Any]:

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return response




def _meeting_uuid(meeting_id: str | None):
    if not meeting_id:
        return None
    try:
        from uuid import UUID

        return UUID(meeting_id)
    except ValueError:
        return None


async def _find_bot_session(meeting_id: str, settings: Settings) -> BotSession | None:
    meeting_uuid = _meeting_uuid(meeting_id)
    if meeting_uuid is None or not settings.database_url:
        return None
    try:
        async for session in get_session(settings):
            return await session.scalar(
                select(BotSession).where(BotSession.meeting_id == meeting_uuid)
            )
    except (SQLAlchemyError, OSError):
        return None
    return None


async def _save_bot_session(
    meeting_id: str, bot_id: str, status: str, meeting_url: str, settings: Settings
) -> None:
    meeting_uuid = _meeting_uuid(meeting_id)
    if meeting_uuid is None or not settings.database_url:
        return

    try:
        async for session in get_session(settings):
            existing = await session.scalar(
                select(BotSession).where(BotSession.meeting_id == meeting_uuid)
            )
            if existing is None:
                session.add(
                    BotSession(
                        meeting_id=meeting_uuid,
                        provider_bot_id=bot_id,
                        status=status,
                        meeting_url=meeting_url,
                    )
                )
            else:
                existing.provider_bot_id = bot_id
                existing.status = status
                existing.meeting_url = meeting_url
            await session.commit()
            return
    except SQLAlchemyError:
        return


async def _persist_provider_transcript(
    meeting_id: str | None, payload: dict[str, Any], settings: Settings
) -> None:
    """Persist transcript events emitted by Meeting BaaS when they use JSON frames."""
    meeting_uuid = _meeting_uuid(meeting_id)
    if meeting_uuid is None or not settings.database_url:
        return
    text_value = payload.get("text") or payload.get("transcript") or payload.get("content")
    if not isinstance(text_value, str) or not text_value.strip():
        return
    speaker = payload.get("speaker") or payload.get("speaker_label") or "Meeting participant"
    if not isinstance(speaker, str):
        speaker = "Meeting participant"
    now = datetime.now(UTC)
    try:
        async for session in get_session(settings):
            latest = await session.scalar(
                select(func.max(Transcript.sequence)).where(Transcript.meeting_id == meeting_uuid)
            )
            confidence = payload.get("confidence")
            session.add(
                Transcript(
                    meeting_id=meeting_uuid,
                    speaker_label=speaker[:255],
                    sequence=int(latest or 0) + 1,
                    started_at=now,
                    ended_at=now,
                    text=text_value.strip()[:20_000],
                    source="meeting_baas",
                    confidence=confidence if isinstance(confidence, (int, float)) else None,
                )
            )
            await session.commit()
            return
    except SQLAlchemyError:
        return


async def _mark_bot_status(bot_id: str, status: str, settings: Settings) -> None:
    """Keep the local BotSession aligned with provider lifecycle changes."""
    if not settings.database_url:
        return
    try:
        async for session in get_session(settings):
            existing = await session.scalar(
                select(BotSession).where(BotSession.provider_bot_id == bot_id)
            )
            if existing is not None:
                existing.status = status
                await session.commit()
            return
    except SQLAlchemyError:
        return


# ============================================================
# Join Meeting
# ============================================================


@router.post(
    "/join",
    response_model=JoinMeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_meeting(
    request: JoinMeetingRequest,
    idempotency_key_header: str | None = Header(
        None,
        alias="Idempotency-Key",
    ),
    client: MeetingBaasClient = Depends(
        get_meeting_baas_client
    ),
) -> JoinMeetingResponse:

    key = _idempotency_key(
        request.meeting_url,
        idempotency_key_header,
        request.meeting_id,
    )

    if request.meeting_id:
        existing = await _find_bot_session(request.meeting_id, client.settings)
        if existing and existing.provider_bot_id:
            if existing.status not in {"left", "ended", "completed", "failed"}:
                return JoinMeetingResponse(
                    bot_id=existing.provider_bot_id,
                    status=existing.status,
                    idempotency_key=key,
                )
            # A terminal provider session must not be reused on the next join.
            join_registry._responses.pop(key, None)

    payload: dict[str, Any] = {
        "meeting_url": str(request.meeting_url),
        "bot_name": "Proximate AI",
        "streaming_enabled": True,
        "streaming_config": {
            "output_url": None,
            "input_url":  _meeting_input_url(client.settings.meeting_baas_input_url, request.meeting_id),
            "audio_frequency": 24000,
        },
    }
    print("\n========== MEETING BAAS CREATE DEBUG ==========")
    print("[MEETBOT] meeting_url =", payload["meeting_url"])
    print("[MEETBOT] bot_name =", payload["bot_name"])
    print("[MEETBOT] streaming_enabled =", payload["streaming_enabled"])
    print("[MEETBOT] input_url =", payload["streaming_config"]["input_url"])
    print("[MEETBOT] audio_frequency =", payload["streaming_config"]["audio_frequency"])
    print("===============================================\n")

    async def create() -> JoinMeetingResponse:
        if not client.settings.meeting_baas_api_key:
            return JoinMeetingResponse(
                status="text_card",
                idempotency_key=key,
                text_card=TextCardFallback(reason="meeting_baas_not_configured"),
            )
        if not client.settings.meeting_baas_input_url:
            # A bot can still join without an input stream, but it cannot receive
            # generated speech. Report this explicitly instead of failing later
            # with a generic WebSocket/503 error when Voice Bot speaks.
            return JoinMeetingResponse(
                status="text_card",
                idempotency_key=key,
                text_card=TextCardFallback(reason="audio_input_not_configured"),
            )

        try:
            provider_bot = await client.create_bot(
                payload,
                idempotency_key=key,
            )
            print("\n========== MEETING BAAS RESPONSE DEBUG ==========")
            print(json.dumps(provider_bot, indent=2, ensure_ascii=False))
            print("==================================================\n")

        except MeetingBaasError:

            return JoinMeetingResponse(
                status="text_card",
                idempotency_key=key,
                text_card=TextCardFallback(
                    reason="voice_bot_unavailable"
                ),
            )

        bot = _provider_data(provider_bot)

        bot_id = (
            bot.get("bot_id")
            or bot.get("id")
        )

        if not isinstance(bot_id, str) or not bot_id:

            return JoinMeetingResponse(
                status="text_card",
                idempotency_key=key,
                text_card=TextCardFallback(
                    reason="voice_bot_unavailable"
                ),
            )

        response = JoinMeetingResponse(
            bot_id=bot_id,
            status="pending",
            idempotency_key=key,
        )
        if request.meeting_id:
            await _save_bot_session(
                request.meeting_id,
                bot_id,
                "pending",
                str(request.meeting_url),
                client.settings,
            )
        return response

    return await join_registry.get_or_create(
        key,
        create,
    )


@router.get("/meeting/{meeting_id}", response_model=BotStatusResponse)
async def get_meeting_bot_status(
    meeting_id: str,
    client: MeetingBaasClient = Depends(get_meeting_baas_client),
) -> BotStatusResponse:
    """Return the persisted provider Bot for a meeting after a page refresh."""
    existing = await _find_bot_session(meeting_id, client.settings)
    if existing is None or not existing.provider_bot_id:
        raise HTTPException(status_code=404, detail="meeting bot not found")
    if existing.status in {"left", "ended", "failed"}:
        raise HTTPException(status_code=404, detail="meeting bot is no longer active")
    try:
        provider_response = await client.get_bot(existing.provider_bot_id)
        provider = _provider_data(provider_response)
        provider_status = provider.get("status")
        status_value = provider_status if isinstance(provider_status, str) else existing.status
    except MeetingBaasError:
        status_value = existing.status
    if status_value != existing.status:
        try:
            async for session in get_session(client.settings):
                row = await session.scalar(
                    select(BotSession).where(BotSession.meeting_id == existing.meeting_id)
                )
                if row:
                    row.status = status_value
                    await session.commit()
                break
        except SQLAlchemyError:
            pass
    return BotStatusResponse(bot_id=existing.provider_bot_id, status=status_value)


# ============================================================
# Bot Status
# ============================================================


@router.get(
    "/{bot_id}",
    response_model=BotStatusResponse,
)
async def get_bot_status(
    bot_id: str,
    client: MeetingBaasClient = Depends(
        get_meeting_baas_client
    ),
) -> BotStatusResponse:

    try:

        response = await client.get_bot(
            bot_id
        )

    except MeetingBaasError as exc:

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.code,
        ) from None

    bot = _provider_data(response)

    bot_status = bot.get("status")

    if not isinstance(bot_status, str):
        bot_status = "unknown"

    return BotStatusResponse(
        bot_id=bot_id,
        status=bot_status,
    )


# ============================================================
# Leave Meeting
# ============================================================


@router.post(
    "/{bot_id}/leave",
    response_model=LeaveMeetingResponse,
)
async def leave_meeting(
    bot_id: str,
    client: MeetingBaasClient = Depends(
        get_meeting_baas_client
    ),
) -> LeaveMeetingResponse:

    try:

        await client.leave_bot(
            bot_id
        )

    except MeetingBaasError as exc:

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.code,
        ) from None

    await _mark_bot_status(bot_id, "left", client.settings)

    return LeaveMeetingResponse(
        bot_id=bot_id
    )



# ============================================================
# Speak
# ============================================================

async def speak_text_to_meeting(
    text: str,
    meeting_id: str,
    settings: Settings,
) -> None:
    render_speak_url = (
        f"{settings.websocket_service_url.rstrip('/')}/speak"
    )

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10,
                read=60,
                write=10,
                pool=10,
            )
        ) as http_client:
            response = await http_client.post(
                render_speak_url,
                json={
                    "text": text,
                    "meeting_id": meeting_id,
                },
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Render speak service error: "
                f"{response.text}"
            )

    except httpx.TimeoutException:
        raise RuntimeError(
            "Render speak service timeout"
        ) from None

    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Render speak service unavailable: {exc}"
        ) from exc


async def text_to_speech(text: str, output_file: Path) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    mp3_file = output_file.with_suffix(".mp3")

    try:
        print("[TTS] 開始 Edge TTS...")

        communicate = edge_tts.Communicate(
            text=text,
            voice="zh-TW-HsiaoChenNeural",
        )

        await communicate.save(str(mp3_file))

        print("[TTS] Edge TTS 完成")

        if not mp3_file.exists():
            raise RuntimeError("Edge TTS 沒有產生 MP3")

        mp3_size = mp3_file.stat().st_size

        print(f"[TTS] MP3 大小: {mp3_size} bytes")

        if mp3_size == 0:
            raise RuntimeError("Edge TTS 回傳空音訊")

        print("[TTS] 開始 miniaudio 解碼...")

        def decode_mp3() -> bytes:
            decoded = miniaudio.decode_file(
                str(mp3_file),
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=1,
                sample_rate=24000,
            )

            return bytes(decoded.samples)

        pcm_data = await asyncio.to_thread(decode_mp3)

        if not pcm_data:
            raise RuntimeError("miniaudio 沒有產生 PCM 音訊")

        print(
            f"[TTS] PCM 大小: {len(pcm_data)} bytes"
        )

        # 建立 WAV header
        import wave

        def write_wav() -> None:
            with wave.open(str(output_file), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)  # signed 16-bit
                wav.setframerate(24000)
                wav.writeframes(pcm_data)

        await asyncio.to_thread(write_wav)

        if not output_file.exists():
            raise RuntimeError("沒有產生 WAV")

        print(
            f"[TTS] WAV 完成: {output_file.stat().st_size} bytes"
        )

        return output_file

    except Exception as exc:
        raise RuntimeError(
            f"TTS 音訊轉換失敗: {type(exc).__name__}: {exc}"
        ) from exc

    finally:
        mp3_file.unlink(missing_ok=True)


@router.post("/speak")
async def speak(
    request: SpeakRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    render_speak_url = f"{settings.websocket_service_url.rstrip('/')}/speak"

    print("\n========== SPEAK DEBUG START ==========")
    print(f"[1] 收到文字: {request.text}")
    print(f"[2] Meeting ID: {request.meeting_id}")
    print(f"[3] Render Speak URL: {render_speak_url}")

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10,
                read=60,
                write=10,
                pool=10,
            )
        ) as http_client:
            response = await http_client.post(
                render_speak_url,
                json={
                    "text": request.text,
                    "meeting_id": request.meeting_id,
                },
            )

        if response.status_code >= 400:
            print(
                f"[ERROR] Render /speak "
                f"status={response.status_code} "
                f"body={response.text}"
            )

            raise HTTPException(
                status_code=503,
                detail=f"Render speak service error: {response.text}",
            )

        print("[4] Render TTS / WebSocket 傳送成功")
        print("========== SPEAK DEBUG SUCCESS ==========\n")

        return response.json()

    except httpx.TimeoutException as exc:
        print(f"[ERROR] Render /speak timeout: {exc}")

        raise HTTPException(
            status_code=504,
            detail="Render speak service timeout",
        ) from None

    except httpx.RequestError as exc:
        print(f"[ERROR] Render /speak request failed: {exc}")

        raise HTTPException(
            status_code=503,
            detail=f"Render speak service unavailable: {exc}",
        ) from None