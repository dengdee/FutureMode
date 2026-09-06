"""Compatibility routes for the Meeting BaaS voice-bot integration."""

import asyncio
import hashlib
import subprocess
import tempfile
import wave
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field, HttpUrl

from app.config import Settings, get_settings
from app.integrations.meetingbaas import MeetingBaasClient, MeetingBaasError

settings = get_settings()
router = APIRouter(prefix="/meetbot", tags=["meetbot"])

class JoinMeetingRequest(BaseModel):
    meeting_url: HttpUrl


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


class AudioInputManager:
    """Holds the active Meeting BaaS input socket for the existing WAV playback flow."""

    def __init__(self) -> None:
        self.websocket: WebSocket | None = None

    async def send_wav(self, wav_path: Path) -> None:
        if self.websocket is None:
            raise RuntimeError("Meeting BaaS 尚未連接 /meetbot/ws/audio-in")
        with wave.open(str(wav_path), "rb") as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 24000:
                raise ValueError("語音檔必須為 24 kHz、mono、16-bit PCM WAV")
            while pcm_data := wav.readframes(2400):
                await self.websocket.send_bytes(pcm_data)
                await asyncio.sleep(0.1)


audio_manager = AudioInputManager()


class _JoinRegistry:
    """Process-local duplicate protection until bot_sessions persistence is wired in."""

    def __init__(self) -> None:
        self._responses: dict[str, JoinMeetingResponse] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        key: str,
        create: Callable[[], Awaitable[JoinMeetingResponse]],
    ) -> JoinMeetingResponse:
        async with self._lock:
            if existing := self._responses.get(key):
                return existing
            response = await create()
            if response.bot_id:
                self._responses[key] = response
            return response


join_registry = _JoinRegistry()


def get_meeting_baas_client(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[MeetingBaasClient]:
    yield MeetingBaasClient(settings)


def _idempotency_key(meeting_url: HttpUrl, supplied_key: str | None) -> str:
    if supplied_key and supplied_key.strip():
        return supplied_key.strip()
    # Legacy clients do not send a key. The stable URL-derived key protects them too.
    return hashlib.sha256(str(meeting_url).encode()).hexdigest()


def _provider_data(response: dict[str, Any]) -> dict[str, Any]:
    """Meeting BaaS v2 returns successful payloads in a ``data`` envelope."""
    data = response.get("data")
    return data if isinstance(data, dict) else response


@router.post("/join", response_model=JoinMeetingResponse, status_code=status.HTTP_201_CREATED)
async def join_meeting(
    request: JoinMeetingRequest,
    idempotency_key_header: str | None = Header(None, alias="Idempotency-Key"),
    client: MeetingBaasClient = Depends(get_meeting_baas_client),
) -> JoinMeetingResponse:
    """Join once, returning a stable result rather than raw provider JSON."""
    key = _idempotency_key(request.meeting_url, idempotency_key_header)
    payload: dict[str, Any] = {
        "meeting_url": str(request.meeting_url),
        "bot_name": "Proximate AI",
        "streaming_enabled": True,
        "streaming_config": {
            "output_url": None,
            "input_url": client.settings.meeting_baas_input_url,
            "audio_frequency": 24000,
        },
    }
    async def create() -> JoinMeetingResponse:
        try:
            provider_bot = await client.create_bot(payload, idempotency_key=key)
        except MeetingBaasError:
            # Provider details are intentionally neither returned nor logged here.
            return JoinMeetingResponse(
                status="text_card",
                idempotency_key=key,
                text_card=TextCardFallback(reason="voice_bot_unavailable"),
            )
        bot = _provider_data(provider_bot)
        bot_id = bot.get("bot_id") or bot.get("id")
        if not isinstance(bot_id, str) or not bot_id:
            return JoinMeetingResponse(
                status="text_card",
                idempotency_key=key,
                text_card=TextCardFallback(reason="voice_bot_unavailable"),
            )
        return JoinMeetingResponse(bot_id=bot_id, status="pending", idempotency_key=key)

    return await join_registry.get_or_create(key, create)


@router.get("/{bot_id}", response_model=BotStatusResponse)
async def get_bot_status(
    bot_id: str,
    client: MeetingBaasClient = Depends(get_meeting_baas_client),
) -> BotStatusResponse:
    try:
        provider_bot = await client.get_bot(bot_id)
    except MeetingBaasError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from None
    bot = _provider_data(provider_bot)
    provider_status = bot.get("status")
    return BotStatusResponse(
        bot_id=str(bot.get("bot_id") or bot.get("id") or bot_id),
        status=provider_status if isinstance(provider_status, str) else "unknown",
    )


@router.post("/{bot_id}/leave", response_model=LeaveMeetingResponse)
async def leave_meeting(
    bot_id: str,
    client: MeetingBaasClient = Depends(get_meeting_baas_client),
) -> LeaveMeetingResponse:
    try:
        await client.leave_bot(bot_id)
    except MeetingBaasError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from None
    return LeaveMeetingResponse(bot_id=bot_id)




class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)

async def text_to_speech(text: str, output_file: Path) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    temp_file = output_file.with_suffix(".mp3")

    try:
        try:
            import edge_tts
        except ModuleNotFoundError:
            raise RuntimeError("缺少 edge-tts，請先同步 backend 依賴") from None

        # print("[TTS] 開始 Edge TTS...")

        communicate = edge_tts.Communicate(
            text=text,
            voice="zh-TW-HsiaoChenNeural",
        )

        await communicate.save(str(temp_file))

        # print("[TTS] Edge TTS 完成")

        if not temp_file.exists():
            raise RuntimeError("Edge TTS 沒有產生 MP3")

        # print(
        #     f"[TTS] MP3 大小: {temp_file.stat().st_size} bytes"
        # )

        if temp_file.stat().st_size == 0:
            raise RuntimeError("Edge TTS 回傳空音訊")

        # print("[TTS] 開始 FFmpeg 轉換 WAV...")

        await asyncio.to_thread(
            subprocess.run,
            [
                "ffmpeg",
                "-y",
                "-i",
                str(temp_file),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                str(output_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        if not output_file.exists():
            raise RuntimeError("FFmpeg 沒有產生 WAV")

        # print(
        #     f"[TTS] WAV 大小: {output_file.stat().st_size} bytes"
        # )

        return output_file

    except FileNotFoundError:
        raise RuntimeError(
            "找不到 ffmpeg，請確認 ffmpeg 已安裝並加入 PATH"
        ) from None

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffmpeg 轉換失敗: {exc.stderr}"
        ) from None

    except Exception as exc:
        raise RuntimeError(
            f"Edge TTS 失敗: {type(exc).__name__}: {exc}"
        ) from None

    finally:
        temp_file.unlink(missing_ok=True)


async def speak_text_to_meeting(text: str) -> None:
    """Generate a temporary 24 kHz mono WAV and stream it to the meeting input."""
    if audio_manager.websocket is None:
        raise RuntimeError("Meeting BaaS 尚未連接 /meetbot/ws/audio-in")
    with tempfile.NamedTemporaryFile(prefix="proximate-tts-", suffix=".wav", delete=False) as temp:
        output_file = Path(temp.name)
    try:
        await text_to_speech(text, output_file)
        await audio_manager.send_wav(output_file)
    finally:
        output_file.unlink(missing_ok=True)


@router.websocket("/ws/audio-in")
async def meeting_audio_input(websocket: WebSocket) -> None:
    """Accept the provider's input-audio connection without logging its headers."""
    await websocket.accept()
    audio_manager.websocket = websocket

    try:
        while True:
            await websocket.receive()

    except WebSocketDisconnect:
        pass

    finally:
        if audio_manager.websocket is websocket:
            audio_manager.websocket = None


@router.post("/speak")
async def speak(request: SpeakRequest) -> dict[str, str]:
    # print("\n========== SPEAK DEBUG START ==========")
    # print(f"[1] 收到文字: {request.text}")

    try:
        # print("[2] 開始 TTS...")

        await speak_text_to_meeting(request.text)

        # print("[6] WAV 傳送完成")
        # print("========== SPEAK DEBUG SUCCESS ==========\n")

        return {
            "status": "sent",
            "message": "Audio sent to meeting",
        }

    except RuntimeError as exc:
        # print(f"[ERROR] {exc}")

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from None

    except Exception as exc:
        # print(
        #     f"[ERROR] {type(exc).__name__}: {exc}"
        # )

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from None

    # finally:
    #     output_file.unlink(missing_ok=True)

        # print("========== SPEAK DEBUG END ==========\n")
