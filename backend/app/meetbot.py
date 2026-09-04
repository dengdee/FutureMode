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
