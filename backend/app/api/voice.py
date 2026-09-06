"""Authenticated meeting Voice Bot request and host-control endpoints."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetbot import speak_text_to_meeting
from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.models import VoiceRequest
from app.realtime.gateway import publish_realtime_event
from app.schemas.events import MeetingEvent
from app.schemas.meeting import (
    VoiceBotStatusResponse,
    VoiceHostAction,
    VoiceRequestCreate,
    VoiceSpeakRequest,
)
from app.services.llm import LLMConfigurationError, LLMProviderError, generate_meeting_speech

router = APIRouter(prefix="/api/v1", tags=["voice-bot"])


async def _latest_request(meeting_id: UUID, session: AsyncSession) -> VoiceRequest | None:
    return await session.scalar(
        select(VoiceRequest)
        .where(VoiceRequest.meeting_id == meeting_id)
        .order_by(VoiceRequest.created_at.desc())
    )


def _response(
    meeting_id: UUID,
    request: VoiceRequest | None,
    *,
    message: str | None = None,
    generated_text: str | None = None,
) -> VoiceBotStatusResponse:
    return VoiceBotStatusResponse(
        meeting_id=meeting_id,
        status=request.status if request else "not_requested",
        request_id=request.id if request else None,
        approved_text_version=request.approved_text_version if request else None,
        message=message,
        generated_text=generated_text,
    )


async def _publish(request: Request, meeting_id: UUID, state: VoiceBotStatusResponse) -> None:
    event = MeetingEvent(
        event_id=uuid4(),
        meeting_id=meeting_id,
        timestamp=datetime.now(UTC),
        schema_version=1,
        payload={
            "type": "voice_bot:status",
            "status": state.status,
            "request_id": str(state.request_id) if state.request_id else None,
            "approved_text_version": state.approved_text_version,
            "message": state.message,
            "generated_text": state.generated_text,
        },
    )
    await publish_realtime_event(
        request.app.state.event_journal,
        request.app.state.room_registry,
        event,
        broker=request.app.state.realtime_broker,
    )


@router.get("/meetings/{meeting_id}/voice-bot/status", response_model=VoiceBotStatusResponse)
async def voice_status(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> VoiceBotStatusResponse:
    await authorized_meeting(meeting_id, principal, session)
    try:
        return _response(meeting_id, await _latest_request(meeting_id, session))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.post(
    "/meetings/{meeting_id}/voice-bot/request",
    response_model=VoiceBotStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_voice(
    meeting_id: UUID,
    payload: VoiceRequestCreate,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> VoiceBotStatusResponse:
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    voice_request = VoiceRequest(
        meeting_id=meeting_id,
        requester_user_id=user_id,
        status="waiting_for_votes",
        approved_text=payload.approved_text,
        approved_text_version=1 if payload.approved_text else 0,
    )
    session.add(voice_request)
    try:
        await session.commit()
        await session.refresh(voice_request)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    response = _response(meeting_id, voice_request)
    await _publish(request, meeting_id, response)
    return response


@router.post("/meetings/{meeting_id}/voice-bot/host-action", response_model=VoiceBotStatusResponse)
async def host_action(
    meeting_id: UUID,
    payload: VoiceHostAction,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> VoiceBotStatusResponse:
    await authorized_meeting(meeting_id, principal, session, write=True)
    voice_request = await _latest_request(meeting_id, session)
    if voice_request is None:
        raise HTTPException(status_code=404, detail="voice request not found")
    next_status = {
        "approve": "approved",
        "reject": "failed",
        "retry": "waiting_for_votes",
        "pause": "waiting_for_host",
        "resume": "approved",
    }[payload.action]
    voice_request.status = next_status
    try:
        await session.commit()
        await session.refresh(voice_request)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    response = _response(meeting_id, voice_request)
    await _publish(request, meeting_id, response)
    return response


@router.post(
    "/meetings/{meeting_id}/voice-bot/generate-and-speak",
    response_model=VoiceBotStatusResponse,
)
async def generate_and_speak(
    meeting_id: UUID,
    payload: VoiceSpeakRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
    settings: Settings = Depends(get_settings),
) -> VoiceBotStatusResponse:
    """Generate an approved meeting contribution, synthesize it, and stream it to Meet."""
    await authorized_meeting(meeting_id, principal, session, write=True)
    voice_request = await _latest_request(meeting_id, session)
    if voice_request is None:
        raise HTTPException(status_code=404, detail="voice request not found")
    if voice_request.status != "approved":
        raise HTTPException(status_code=409, detail="voice request must be approved first")

    prompt = (
        payload.prompt or voice_request.approved_text or "請提出目前議題最重要的觀察與下一步"
    ).strip()
    try:
        generated_text = await generate_meeting_speech(prompt, payload.context, settings)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError:
        raise HTTPException(status_code=502, detail="LLM provider unavailable") from None

    voice_request.status = "preparing_audio"
    voice_request.approved_text = generated_text
    voice_request.approved_text_version += 1
    try:
        await session.commit()
        await session.refresh(voice_request)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    await _publish(
        request,
        meeting_id,
        _response(
            meeting_id,
            voice_request,
            message="正在準備語音。",
            generated_text=generated_text,
        ),
    )

    voice_request.status = "speaking"
    try:
        await session.commit()
        await speak_text_to_meeting(generated_text)
    except RuntimeError as exc:
        await session.rollback()
        voice_request.status = "failed"
        await session.commit()
        failed = _response(
            meeting_id,
            voice_request,
            message=str(exc),
            generated_text=generated_text,
        )
        await _publish(request, meeting_id, failed)
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None

    voice_request.status = "completed"
    try:
        await session.commit()
        await session.refresh(voice_request)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    completed = _response(
        meeting_id,
        voice_request,
        message="Voice Bot 已完成發言。",
        generated_text=generated_text,
    )
    await _publish(request, meeting_id, completed)
    return completed
