import asyncio
import os
from pathlib import Path

import edge_tts
import miniaudio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI(title="Proximate WebSocket Server")


# ============================================================
# WebSocket State
# ============================================================

audio_websocket: WebSocket | None = None


# ============================================================
# Request Models
# ============================================================


class SpeakRequest(BaseModel):
    text: str


# ============================================================
# Health Check
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "websocket": audio_websocket is not None,
    }


# ============================================================
# Meeting BaaS WebSocket
# ============================================================


@app.websocket("/ws/audio-in")
async def audio_input(websocket: WebSocket):
    global audio_websocket

    print("\n========== WEBSOCKET DEBUG START ==========")
    print("[WS] 收到 Meeting BaaS WebSocket 連線")

    try:
        await websocket.accept()

        audio_websocket = websocket

        print("[WS] WebSocket ACCEPT 成功")
        print("[WS] audio_websocket = websocket")
        print("[WS] WebSocket 狀態: CONNECTED")

        while True:
            message = await websocket.receive()

            message_type = message.get("type")

            print(f"[WS] 收到訊息 type={message_type}")

            if message.get("bytes") is not None:
                print(
                    f"[WS] 收到 binary audio: "
                    f"{len(message['bytes'])} bytes"
                )

            elif message.get("text") is not None:
                print(
                    f"[WS] 收到 text: "
                    f"{message['text']}"
                )

    except WebSocketDisconnect as exc:
        print(f"[WS] WebSocket 斷線 code={exc.code}")

    except Exception as exc:
        print(
            f"[WS] WebSocket ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        if audio_websocket is websocket:
            audio_websocket = None

        print("[WS] audio_websocket = None")
        print("[WS] WebSocket CLOSED")
        print("========== WEBSOCKET DEBUG END ==========\n")


# ============================================================
# Edge TTS → PCM
# ============================================================


async def text_to_pcm(text: str) -> bytes:
    print("[TTS] 開始 Edge TTS...")

    temp_dir = Path("/tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 使用 PID + timestamp 避免多 request 撞檔
    filename = (
        f"proximate-tts-"
        f"{os.getpid()}-"
        f"{id(text)}.mp3"
    )

    mp3_file = temp_dir / filename

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice="zh-TW-HsiaoChenNeural",
        )

        await communicate.save(str(mp3_file))

        print("[TTS] Edge TTS 完成")

        if not mp3_file.exists():
            raise RuntimeError(
                "Edge TTS 沒有產生 MP3"
            )

        size = mp3_file.stat().st_size

        print(f"[TTS] MP3 大小: {size} bytes")

        if size == 0:
            raise RuntimeError(
                "Edge TTS 回傳空音訊"
            )

        print("[TTS] 開始 miniaudio 解碼...")

        def decode() -> bytes:
            decoded = miniaudio.decode_file(
                str(mp3_file),
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=1,
                sample_rate=24000,
            )

            return bytes(decoded.samples)

        pcm_data = await asyncio.to_thread(decode)

        if not pcm_data:
            raise RuntimeError(
                "miniaudio 沒有產生 PCM"
            )

        print(
            f"[TTS] PCM 大小: "
            f"{len(pcm_data)} bytes"
        )

        return pcm_data

    finally:
        mp3_file.unlink(missing_ok=True)


# ============================================================
# Speak API
# ============================================================


@app.post("/speak")
async def speak(request: SpeakRequest):
    print("\n========== SPEAK DEBUG START ==========")
    print(f"[1] 收到文字: {request.text}")

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="text 不可以是空的",
        )

    # --------------------------------------------------------
    # Check WebSocket
    # --------------------------------------------------------

    print(
        "[2] Meeting BaaS WebSocket:",
        audio_websocket is not None,
    )

    if audio_websocket is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Meeting BaaS 尚未連接 "
                "/ws/audio-in"
            ),
        )

    try:
        # ----------------------------------------------------
        # TTS
        # ----------------------------------------------------

        print("[3] 開始 TTS...")

        pcm_data = await text_to_pcm(
            request.text
        )

        print("[4] TTS 完成")

        # ----------------------------------------------------
        # Send PCM
        # ----------------------------------------------------

        print(
            "[5] 開始傳送 PCM "
            f"({len(pcm_data)} bytes)"
        )

        websocket = audio_websocket

        if websocket is None:
            raise RuntimeError(
                "Meeting BaaS WebSocket 在傳送前斷線"
            )

        await websocket.send_bytes(
            pcm_data
        )

        print("[6] PCM 傳送完成")
        print(
            "========== SPEAK DEBUG SUCCESS ==========\n"
        )

        return {
            "status": "sent",
            "message": "Audio sent to meeting",
            "bytes": len(pcm_data),
            "sample_rate": 24000,
            "channels": 1,
            "format": "s16",
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[ERROR] "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    finally:
        print(
            "========== SPEAK DEBUG END ==========\n"
        )


# ============================================================
# Root
# ============================================================


@app.get("/")
async def root():
    return {
        "service": "Proximate WebSocket Server",
        "status": "ok",
    }