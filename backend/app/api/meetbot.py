import httpx
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, HttpUrl
import asyncio
import wave
from pathlib import Path


from app.config import get_settings

router = APIRouter(
    prefix="/meetbot",
    tags=["meetbot"],
)

settings = get_settings()

class JoinMeetingRequest(BaseModel):
    meeting_url: HttpUrl

class LeaveMeetingRequest(BaseModel):
    bot_id: str


BASE_DIR = Path(__file__).resolve().parent.parent
HELLO_WAV = BASE_DIR /"audio" / "hello.wav"

print("HELLO_WAV =", HELLO_WAV)
print("EXISTS =", HELLO_WAV.exists())


# =========================
# Audio Input Manager
# =========================

class AudioInputManager:
    def __init__(self):
        self.websocket: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.websocket = websocket

        print("================================")
        print("Meeting BaaS Audio Input Connected")
        print("================================")

    async def disconnect(self):
        self.websocket = None

        print("================================")
        print("Meeting BaaS Audio Input Disconnected")
        print("================================")

    async def send_pcm(self, pcm_data: bytes):
        if self.websocket is None:
            raise RuntimeError(
                "Meeting BaaS 尚未連接 /ws/audio-in"
            )

        await self.websocket.send_bytes(pcm_data)

    async def send_wav(self, wav_path: str):
        if self.websocket is None:
            raise RuntimeError(
                "Meeting BaaS 尚未連接 /ws/audio-in"
            )

        print(f"開始播放：{wav_path}")

        with wave.open(wav_path, "rb") as wav:

            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()

            print(f"channels    = {channels}")
            print(f"sample_width = {sample_width * 8} bit")
            print(f"sample_rate = {sample_rate} Hz")

            if channels != 1:
                raise ValueError("WAV 必須是 Mono")

            if sample_width != 2:
                raise ValueError("WAV 必須是 16-bit PCM")

            if sample_rate != 24000:
                raise ValueError(
                    f"WAV 必須是 24000 Hz，目前是 {sample_rate} Hz"
                )

            # 2400 samples = 100 ms @ 24 kHz
            chunk_size = 2400

            while True:

                pcm_data = wav.readframes(chunk_size)

                if not pcm_data:
                    break

                # 只傳 raw PCM
                await self.websocket.send_bytes(pcm_data)

                # 讓播放速度接近即時
                await asyncio.sleep(0.1)

        print("音訊播放完成")


audio_manager = AudioInputManager()



# =========================
# Helper
# =========================

def get_headers() -> dict[str, str]:
    if not settings.meeting_baas_api_key:
        raise HTTPException(
            status_code=503,
            detail="Meeting BaaS 尚未設定",
        )

    return {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": settings.meeting_baas_api_key,
    }

# =========================
# Join Meeting
# =========================
@router.post("/join")
async def join_meeting(request: JoinMeetingRequest):
    if not settings.meeting_baas_api_key:
        raise HTTPException(
            status_code=503,
            detail="Meeting BaaS 尚未設定",
        )

    headers = {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": settings.meeting_baas_api_key,
    }

    payload = {
        "meeting_url": str(request.meeting_url),
        "bot_name": "Proximate AI",

        "streaming_enabled": True,
        "streaming_config": {
            "output_url": None,
            "input_url": settings.meeting_baas_input_url,
            "audio_frequency": 24000
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.meeting_baas_url,
                headers=headers,
                json=payload,
            )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Meeting BaaS connection failed: {exc}",
        ) from exc

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()

# =========================
# Get Bot
# =========================

@router.get("/{bot_id}")
async def get_bot(bot_id: str):
    """
    查詢 Bot 狀態。
    """

    headers = get_headers()

    url = f"{settings.meeting_baas_url}/{bot_id}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=headers,
            )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Meeting BaaS connection failed: {exc}",
        ) from exc

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    try:
        return response.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Meeting BaaS returned invalid JSON",
        ) from None

@router.post("/{bot_id}/leave")
async def leave_meeting(bot_id: str):
    """
    讓 Meeting BaaS Bot 離開目前的會議。
    """

    headers = get_headers()

    url = f"{settings.meeting_baas_url}/{bot_id}/leave"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json={},
            )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Meeting BaaS connection failed: {exc}",
        ) from exc

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    try:
        return response.json()
    except ValueError:
        return {
            "success": True,
            "bot_id": bot_id,
            "response": response.text,
        }


@router.websocket("/ws/meeting")
async def meeting_transcription(websocket: WebSocket):
    await websocket.accept()

    print("Meeting BaaS WebSocket connected")

    try:
        while True:

            event = await websocket.receive_json()

            print("\n===== STT =====")
            print(event)

            if event.get("event") != "transcript.segment":
                continue

            data = event.get("data", {})

            text = data.get("text")
            is_final = data.get("isFinal")

            speaker = data.get("speaker", {})

            speaker_name = speaker.get("name")
            speaker_id = speaker.get("id")

            start = data.get("utteranceStart")
            end = data.get("utteranceEnd")

            if text:
                print(
                    f"[{start:.2f}s - {end:.2f}s] "
                    f"{speaker_name}: {text}"
                )

    except WebSocketDisconnect:
        print("Meeting BaaS WebSocket disconnected")

# =========================
# Meeting BaaS Audio Input
# =========================
@router.websocket("/ws/audio-in")
async def meeting_audio_input(websocket: WebSocket):
    print("================================")
    print("WebSocket request received")
    print("client =", websocket.client)
    print("headers =", dict(websocket.headers))
    print("================================")

    await websocket.accept()

    audio_manager.websocket = websocket

    print("================================")
    print("Meeting BaaS Audio Input Connected")
    print("audio_manager.websocket =", audio_manager.websocket)
    print("================================")

    try:
        while True:
            message = await websocket.receive()

            print(
                "WebSocket message:",
                message.get("type"),
                "bytes=",
                len(message.get("bytes") or b""),
            )

    except WebSocketDisconnect as exc:
        print("================================")
        print("Meeting BaaS Audio Input Disconnected")
        print("code =", exc.code)
        print("================================")

        if audio_manager.websocket is websocket:
            audio_manager.websocket = None

    except Exception as exc:
        print("================================")
        print("WebSocket error:", repr(exc))
        print("================================")

        if audio_manager.websocket is websocket:
            audio_manager.websocket = None

@router.post("/speak")
async def speak():
    print("================================")
    print("SPEAK REQUEST")
    print("audio_manager.websocket =", audio_manager.websocket)
    print("================================")

    try:
        await audio_manager.send_wav(str(HELLO_WAV))

        return {
            "success": True,
            "message": "Audio sent to meeting",
        }

    except RuntimeError as exc:
        print("SPEAK RuntimeError:", repr(exc))
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except ValueError as exc:
        print("SPEAK ValueError:", repr(exc))
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except FileNotFoundError:
        print("SPEAK FileNotFoundError")
        raise HTTPException(
            status_code=404,
            detail="找不到 audio/hello.wav",
        )

    except Exception as exc:
        print("SPEAK ERROR:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Audio sending failed: {exc}",
        )