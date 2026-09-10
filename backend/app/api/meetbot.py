"""Compatibility routes for the Meeting BaaS voice-bot integration."""

import asyncio
import hashlib
import json
import subprocess
import tempfile
import wave
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
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
# Audio Input Manager
# ============================================================


class AudioInputManager:
    """
    Holds the active Meeting BaaS input WebSocket.

    NOTE:
    This is process-local memory.

    It is suitable for the current single-bot PoC,
    but it is NOT a durable multi-instance solution for Vercel.
    """

    def __init__(self) -> None:
        self.websocket: WebSocket | None = None
        self._websockets: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, meeting_id: str | None = None) -> None:
        async with self._lock:
            key = meeting_id or "default"
            previous = self._websockets.get(key)
            self._websockets[key] = websocket
            self.websocket = websocket
        if previous is not None and previous is not websocket:
            try:
                await previous.close(code=1000)
            except Exception:
                pass

    async def disconnect(self, websocket: WebSocket, meeting_id: str | None = None) -> None:
        async with self._lock:
            key = meeting_id or "default"
            if self._websockets.get(key) is websocket:
                self._websockets.pop(key, None)
            if self.websocket is websocket:
                self.websocket = next(iter(self._websockets.values()), None)

    async def send_wav(self, wav_path: Path, meeting_id: str | None = None) -> None:
        async with self._lock:
            websocket = self._websockets.get(meeting_id or "default")
            if websocket is None and meeting_id is None:
                websocket = self.websocket

        if websocket is None:
            raise RuntimeError(
                "Meeting BaaS 尚未連接 /meetbot/ws/audio-in；請先建立本場會議的音訊連線"
            )

        with wave.open(str(wav_path), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()

            if channels != 1:
                raise ValueError(
                    f"語音檔必須為 mono，目前 channels={channels}"
                )

            if sample_width != 2:
                raise ValueError(
                    f"語音檔必須為 16-bit PCM，目前 sample_width={sample_width}"
                )

            if sample_rate != 24000:
                raise ValueError(
                    f"語音檔必須為 24 kHz，目前 sample_rate={sample_rate}"
                )

            while True:
                pcm_data = wav.readframes(2400)

                if not pcm_data:
                    break

                try:
                    await websocket.send_bytes(pcm_data)
                except (WebSocketDisconnect, RuntimeError, OSError) as exc:
                    await self.disconnect(websocket, meeting_id)
                    raise RuntimeError("Meeting BaaS 音訊 WebSocket 已中斷") from exc

                # 2400 samples / 24000 Hz = 100 ms
                await asyncio.sleep(0.1)


audio_manager = AudioInputManager()


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


def _provider_data(
    response: dict[str, Any],
) -> dict[str, Any]:

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return response


def _meeting_input_url(base_url: str | None, meeting_id: str | None) -> str | None:
    """Attach an optional meeting scope without breaking existing provider URLs."""
    if not base_url or not meeting_id:
        return base_url
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["meeting_id"] = meeting_id
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


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
            "input_url": _meeting_input_url(
                client.settings.meeting_baas_input_url, request.meeting_id
            ),
            "audio_frequency": 24000,
        },
    }

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
# Text To Speech
# ============================================================


async def text_to_speech(
    text: str,
    output_file: Path,
) -> Path:

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = output_file.with_suffix(
        ".mp3"
    )

    try:

        # ----------------------------------------------------
        # Edge TTS
        # ----------------------------------------------------

        try:

            import edge_tts

        except ModuleNotFoundError:

            raise RuntimeError(
                "缺少 edge-tts，請先安裝 backend 依賴"
            ) from None

        communicate = edge_tts.Communicate(
            text=text,
            voice="zh-TW-HsiaoChenNeural",
        )

        await communicate.save(
            str(temp_file)
        )

        if not temp_file.exists():

            raise RuntimeError(
                "Edge TTS 沒有產生 MP3"
            )

        if temp_file.stat().st_size == 0:

            raise RuntimeError(
                "Edge TTS 回傳空音訊"
            )

        # ----------------------------------------------------
        # FFmpeg
        #
        # 不直接依賴 Vercel 系統 PATH 裡的 ffmpeg。
        # 使用 imageio-ffmpeg 提供的 binary。
        # ----------------------------------------------------

        try:

            import imageio_ffmpeg

            ffmpeg_path = (
                imageio_ffmpeg.get_ffmpeg_exe()
            )

        except ModuleNotFoundError:

            raise RuntimeError(
                "缺少 imageio-ffmpeg，請先安裝 backend 依賴"
            ) from None

        await asyncio.to_thread(
            subprocess.run,
            [
                ffmpeg_path,
                "-y",
                "-i",
                str(temp_file),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                "-f",
                "wav",
                str(output_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        if not output_file.exists():

            raise RuntimeError(
                "FFmpeg 沒有產生 WAV"
            )

        if output_file.stat().st_size == 0:

            raise RuntimeError(
                "FFmpeg 產生空 WAV"
            )

        return output_file

    except FileNotFoundError:

        raise RuntimeError(
            "找不到 FFmpeg executable"
        ) from None

    except subprocess.CalledProcessError as exc:

        stderr = (
            exc.stderr
            if isinstance(exc.stderr, str)
            else ""
        )

        raise RuntimeError(
            f"FFmpeg 轉換失敗: {stderr}"
        ) from None

    except Exception as exc:

        if isinstance(exc, RuntimeError):
            raise

        raise RuntimeError(
            f"Edge TTS 失敗: "
            f"{type(exc).__name__}: {exc}"
        ) from None

    finally:

        temp_file.unlink(
            missing_ok=True
        )


# ============================================================
# Speak
# ============================================================


async def speak_text_to_meeting(
    text: str,
    meeting_id: str | None = None,
) -> None:
    with tempfile.NamedTemporaryFile(
        prefix="proximate-tts-",
        suffix=".wav",
        delete=False,
    ) as temp:

        output_file = Path(
            temp.name
        )

    try:

        await text_to_speech(
            text,
            output_file,
        )

        await audio_manager.send_wav(
            output_file,
            meeting_id=meeting_id,
        )

    finally:

        output_file.unlink(
            missing_ok=True
        )

def find_route(routes, target):
    for route in routes:
        path = getattr(route, "path", None)

        if path == target:
            return route

        child_routes = getattr(route, "routes", None)

        if child_routes:
            found = find_route(child_routes, target)
            if found:
                return found

    return None

@router.post("/speak")
async def speak(
    request: Request,
    body: SpeakRequest,
) -> dict[str, str]:
    print("[SPEAK] ===== ROUTES =====", flush=True)

    ws_route = find_route(
        request.app.routes,
        "/meetbot/ws/audio-in",
    )

    print(
        "[SPEAK] WS ROUTE =",
        ws_route,
        "TYPE =",
        type(ws_route).__name__ if ws_route else None,
        flush=True,
    )
    print("[SPEAK] ===== START =====", flush=True)
    print(f"[SPEAK] text={body.text!r}", flush=True)

    try:
        print(
            f"[SPEAK] websocket exists={audio_manager.websocket is not None}",
            flush=True,
        )

        print("[SPEAK] calling speak_text_to_meeting()", flush=True)

        await speak_text_to_meeting(body.text, meeting_id=body.meeting_id)

        print("[SPEAK] audio sent successfully", flush=True)
        print("[SPEAK] ===== SUCCESS =====", flush=True)

        return {
            "status": "sent",
            "message": "Audio sent to meeting",
        }

    except RuntimeError as exc:
        print(
            f"[SPEAK][RuntimeError] {type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from None

    except Exception as exc:
        print(
            f"[SPEAK][Exception] {type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from None

    finally:
        print("[SPEAK] ===== END =====", flush=True)


# ============================================================
# Meeting BaaS Audio Input WebSocket
# ============================================================


@router.websocket(
    "/ws/audio-in"
)
async def meeting_audio_input(
    websocket: WebSocket,
) -> None:

    await websocket.accept()

    meeting_id = websocket.query_params.get("meeting_id")

    await audio_manager.connect(
        websocket,
        meeting_id=meeting_id,
    )

    try:

        while True:

            message = await websocket.receive()

            # Meeting BaaS 可能會送：
            # text / bytes / ping / close
            #
            # 目前只需要維持 connection，
            # 所以不處理內容。

            if message.get("type") == "websocket.disconnect":
                break
            text_frame = message.get("text")
            if isinstance(text_frame, str):
                try:
                    event = json.loads(text_frame)
                except json.JSONDecodeError:
                    event = {}
                if isinstance(event, dict):
                    await _persist_provider_transcript(
                        meeting_id, event, websocket.app.state.settings
                    )

    except WebSocketDisconnect:

        pass

    except Exception:

        # 避免 WebSocket 例外造成整個 request crash
        pass

    finally:

        await audio_manager.disconnect(
            websocket,
            meeting_id=meeting_id,
        )
