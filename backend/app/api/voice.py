"""Authenticated meeting Voice Bot request and host-control endpoints."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetbot import speak_text_to_meeting
from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.models import AISuggestion, Document, DocumentChunk, Transcript, VoiceRequest
from app.realtime.gateway import publish_realtime_event
from app.schemas.events import MeetingEvent
from app.schemas.meeting import (
    VoiceBotStatusResponse,
    VoiceHostAction,
    VoiceObserveRequest,
    VoiceObserveResponse,
    VoiceRequestCreate,
    VoiceSpeakRequest,
)
from app.services.llm import (
    LLMConfigurationError,
    LLMProviderError,
    generate_meeting_observation,
    generate_meeting_speech,
)

router = APIRouter(prefix="/api/v1", tags=["voice-bot"])


def _parse_observation(raw: str) -> tuple[str, str]:
    title = "AI 觀察"
    content = raw.strip()
    for line in raw.splitlines():
        value = line.strip()
        if value.startswith("標題："):
            title = value.removeprefix("標題：").strip() or title
        elif value.startswith("內容："):
            content = value.removeprefix("內容：").strip() or content
    return title[:255], content[:20_000]


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
        await speak_text_to_meeting(generated_text, meeting_id=str(meeting_id))
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


@router.post(
    "/meetings/{meeting_id}/voice-bot/observe",
    response_model=VoiceObserveResponse,
    status_code=status.HTTP_201_CREATED,
)
async def observe_meeting(
    meeting_id: UUID,
    payload: VoiceObserveRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
    settings: Settings = Depends(get_settings),
) -> VoiceObserveResponse:
    """Turn current transcript + published preparation memory into a reviewable suggestion."""
    await authorized_meeting(meeting_id, principal, session)
    transcript = payload.transcript
    if not transcript:
        rows = (
            await session.scalars(
                select(Transcript)
                .where(Transcript.meeting_id == meeting_id)
                .order_by(Transcript.sequence.desc())
                .limit(20)
            )
        ).all()
        transcript = "\n".join(
            f"{row.speaker_label}: {row.text}" for row in reversed(rows)
        )
    if not transcript.strip():
        raise HTTPException(status_code=409, detail="meeting transcript is empty")

    memory_rows = (
        await session.execute(
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.source_type == "preparation",
                Document.status.in_({"ready", "embedded"}),
                Document.metadata_json.contains({"meeting_id": str(meeting_id)}),
            )
            .order_by(DocumentChunk.position)
            .limit(8)
        )
    ).all()
    memory = "\n".join(chunk.content for chunk, _document in memory_rows)
    try:
        raw = await generate_meeting_observation(
            transcript, memory, payload.prompt, settings
        )
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError:
        raise HTTPException(status_code=502, detail="LLM provider unavailable") from None
    title, content = _parse_observation(raw)
    latest_version = await session.scalar(
        select(func.coalesce(func.max(AISuggestion.state_version), 0)).where(
            AISuggestion.meeting_id == meeting_id
        )
    )
    suggestion = AISuggestion(
        meeting_id=meeting_id,
        state_version=int(latest_version or 0) + 1,
        title=title,
        content=content,
        status="pending",
        confidence=0.7 if memory_rows else 0.5,
        suggestion_metadata={
            "source": "meeting_observation",
            "transcript_chars": len(transcript),
            "memory_chunk_ids": [str(chunk.id) for chunk, _document in memory_rows],
        },
    )
    session.add(suggestion)
    try:
        await session.commit()
        await session.refresh(suggestion)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    await publish_realtime_event(
        request.app.state.event_journal,
        request.app.state.room_registry,
        MeetingEvent(
            event_id=uuid4(),
            meeting_id=meeting_id,
            timestamp=datetime.now(UTC),
            schema_version=1,
            payload={
                "type": "ai_suggestion:new",
                "suggestion_id": str(suggestion.id),
                "title": title,
            },
        ),
        broker=request.app.state.realtime_broker,
    )
    return VoiceObserveResponse(
        meeting_id=meeting_id,
        suggestion_id=suggestion.id,
        title=title,
        content=content,
        confidence=suggestion.confidence,
        citations=[
            {"document_id": str(document.id), "chunk_id": str(chunk.id)}
            for chunk, document in memory_rows
        ],
    )
