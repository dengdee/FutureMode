"""Authenticated meeting Voice Bot request and host-control endpoints."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.models import VoiceRequest
from app.realtime.gateway import publish_realtime_event
from app.schemas.events import MeetingEvent
from app.schemas.meeting import VoiceBotStatusResponse, VoiceHostAction, VoiceRequestCreate

router = APIRouter(prefix="/api/v1", tags=["voice-bot"])


async def _latest_request(meeting_id: UUID, session: AsyncSession) -> VoiceRequest | None:
    return await session.scalar(
        select(VoiceRequest)
        .where(VoiceRequest.meeting_id == meeting_id)
        .order_by(VoiceRequest.created_at.desc())
    )


def _response(meeting_id: UUID, request: VoiceRequest | None) -> VoiceBotStatusResponse:
    return VoiceBotStatusResponse(
        meeting_id=meeting_id,
        status=request.status if request else "not_requested",
        request_id=request.id if request else None,
        approved_text_version=request.approved_text_version if request else None,
        message=None,
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


@router.post("/meetings/{meeting_id}/voice-bot/request", response_model=VoiceBotStatusResponse, status_code=status.HTTP_201_CREATED)
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
