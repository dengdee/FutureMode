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

# meeting_id -> WebSocket
audio_websockets: dict[str, WebSocket] = {}


# ============================================================
# Request Models
# ============================================================


class SpeakRequest(BaseModel):
    text: str
    meeting_id: str


# ============================================================
# Health Check
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "websocket_count": len(audio_websockets),
        "meetings": list(audio_websockets.keys()),
    }


# ============================================================
# Meeting BaaS WebSocket
# ============================================================


@app.websocket("/ws/audio-in")
async def audio_input(websocket: WebSocket):
    meeting_id = websocket.query_params.get("meeting_id")

    print("\n========== WEBSOCKET DEBUG START ==========")
    print("[WS] 收到 Meeting BaaS WebSocket 連線")
    print(f"[WS] Meeting ID: {meeting_id}")

    if not meeting_id:
        print("[WS] ERROR: 缺少 meeting_id")

        await websocket.close(
            code=1008,
            reason="meeting_id is required",
        )

        return

    try:
        await websocket.accept()

        # 如果同一個 meeting 已經有舊連線，
        # 新連線直接覆蓋舊連線。
        old_websocket = audio_websockets.get(meeting_id)

        if old_websocket is not None:
            print(
                f"[WS] 發現舊 WebSocket，"
                f"meeting_id={meeting_id}"
            )

            try:
                await old_websocket.close(
                    code=1000,
                    reason="replaced by new connection",
                )
            except Exception:
                pass

        audio_websockets[meeting_id] = websocket

        print("[WS] WebSocket ACCEPT 成功")
        print(
            f"[WS] audio_websockets[{meeting_id}] = websocket"
        )
        print(
            f"[WS] 目前連線數: "
            f"{len(audio_websockets)}"
        )
        print("[WS] WebSocket 狀態: CONNECTED")

        while True:
            message = await websocket.receive()

            message_type = message.get("type")

            print(
                f"[WS] Meeting ID={meeting_id} "
                f"收到訊息 type={message_type}"
            )

            if message.get("bytes") is not None:
                print(
                    f"[WS] Meeting ID={meeting_id} "
                    f"收到 binary audio: "
                    f"{len(message['bytes'])} bytes"
                )

            elif message.get("text") is not None:
                print(
                    f"[WS] Meeting ID={meeting_id} "
                    f"收到 text: "
                    f"{message['text']}"
                )

    except WebSocketDisconnect as exc:
        print(
            f"[WS] WebSocket 斷線 "
            f"meeting_id={meeting_id} "
            f"code={exc.code}"
        )

    except Exception as exc:
        print(
            f"[WS] WebSocket ERROR "
            f"meeting_id={meeting_id}: "
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        # 只有目前這條 connection 才可以刪除
        # 避免舊 connection 斷線時誤刪新 connection。
        if (
            meeting_id
            and audio_websockets.get(meeting_id) is websocket
        ):
            del audio_websockets[meeting_id]

        print(
            f"[WS] 移除 WebSocket "
            f"meeting_id={meeting_id}"
        )
        print(
            f"[WS] 目前連線數: "
            f"{len(audio_websockets)}"
        )
        print("[WS] WebSocket CLOSED")
        print("========== WEBSOCKET DEBUG END ==========\n")


# ============================================================
# Edge TTS → PCM
# ============================================================


async def text_to_pcm(text: str) -> bytes:
    print("[TTS] 開始 Edge TTS...")

    temp_dir = Path("/tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 使用 PID + timestamp / object id 避免多 request 撞檔
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
    print(f"[2] Meeting ID: {request.meeting_id}")

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="text 不可以是空的",
        )

    # --------------------------------------------------------
    # Check WebSocket
    # --------------------------------------------------------

    websocket = audio_websockets.get(
        request.meeting_id
    )

    print(
        "[3] Meeting BaaS WebSocket:",
        websocket is not None,
    )

    print(
        f"[3] 目前 WebSocket 數量: "
        f"{len(audio_websockets)}"
    )

    print(
        f"[3] 目前 Meeting IDs: "
        f"{list(audio_websockets.keys())}"
    )

    if websocket is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Meeting BaaS 尚未連接 "
                f"/ws/audio-in "
                f"(meeting_id={request.meeting_id})"
            ),
        )

    try:
        # ----------------------------------------------------
        # TTS
        # ----------------------------------------------------

        print("[4] 開始 TTS...")

        pcm_data = await text_to_pcm(
            request.text
        )

        print("[5] TTS 完成")

        # ----------------------------------------------------
        # Send PCM
        # ----------------------------------------------------

        print(
            "[6] 開始傳送 PCM "
            f"({len(pcm_data)} bytes)"
        )

        # 再確認一次 connection 沒有被替換
        current_websocket = audio_websockets.get(
            request.meeting_id
        )

        if current_websocket is None:
            raise RuntimeError(
                "Meeting BaaS WebSocket 在傳送前斷線"
            )

        if current_websocket is not websocket:
            websocket = current_websocket

            print(
                "[6] WebSocket 已更新為最新連線"
            )

        await websocket.send_bytes(
            pcm_data
        )

        print("[7] PCM 傳送完成")

        print(
            "========== SPEAK DEBUG SUCCESS ==========\n"
        )

        return {
            "status": "sent",
            "message": "Audio sent to meeting",
            "meeting_id": request.meeting_id,
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
        "websocket_count": len(audio_websockets),
    }