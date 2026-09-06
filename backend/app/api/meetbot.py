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
from app.integrations.meetingbaas import (
    MeetingBaasClient,
    MeetingBaasError,
)


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
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.websocket = websocket

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if self.websocket is websocket:
                self.websocket = None

    async def send_wav(self, wav_path: Path) -> None:
        websocket = self.websocket

        if websocket is None:
            raise RuntimeError(
                "Meeting BaaS 尚未連接 /meetbot/ws/audio-in"
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

                await websocket.send_bytes(pcm_data)

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
) -> str:

    if supplied_key and supplied_key.strip():
        return supplied_key.strip()

    return hashlib.sha256(
        str(meeting_url).encode()
    ).hexdigest()


def _provider_data(
    response: dict[str, Any],
) -> dict[str, Any]:

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return response


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
    )

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

        return JoinMeetingResponse(
            bot_id=bot_id,
            status="pending",
            idempotency_key=key,
        )

    return await join_registry.get_or_create(
        key,
        create,
    )


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
) -> None:

    if audio_manager.websocket is None:

        raise RuntimeError(
            "Meeting BaaS 尚未連接 /meetbot/ws/audio-in"
        )

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
            output_file
        )

    finally:

        output_file.unlink(
            missing_ok=True
        )



@router.post("/speak")
async def speak(request: SpeakRequest) -> dict[str, str]:
    print("[SPEAK] ===== START =====", flush=True)
    print(f"[SPEAK] text={request.text!r}", flush=True)

    try:
        print(
            f"[SPEAK] websocket exists={audio_manager.websocket is not None}",
            flush=True,
        )

        print("[SPEAK] calling speak_text_to_meeting()", flush=True)

        await speak_text_to_meeting(request.text)

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

    await audio_manager.connect(
        websocket
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

    except WebSocketDisconnect:

        pass

    except Exception:

        # 避免 WebSocket 例外造成整個 request crash
        pass

    finally:

        await audio_manager.disconnect(
            websocket
        )