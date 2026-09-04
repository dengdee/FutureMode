import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.config import get_settings

router = APIRouter(
    prefix="/meetbot",
    tags=["meetbot"],
)

settings = get_settings()

MEETING_BAAS_URL = "https://api.meetingbaas.com/v2/bots"

class JoinMeetingRequest(BaseModel):
    meeting_url: HttpUrl

class LeaveMeetingRequest(BaseModel):
    bot_id: str


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
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MEETING_BAAS_URL,
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

    url = f"{MEETING_BAAS_URL}/{bot_id}"

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

    url = f"{MEETING_BAAS_URL}/{bot_id}/leave"

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