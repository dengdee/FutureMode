from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import (
    AgendaItem,
    Meeting,
    MeetingParticipant,
    MeetingState,
    TeamMember,
    Transcript,
    User,
)
from app.schemas.backup import TranscriptBackupRequest
from app.schemas.events import MeetingStateSnapshot, MeetingStateUpdate
from app.schemas.meeting import (
    AgendaItemCreate,
    AgendaItemUpdate,
    MeetingCreate,
    MeetingSummary,
    MeetingUpdate,
    ParticipantAdd,
    ParticipantUpdate,
)
from app.schemas.speech import TranscriptionResponse
from app.services.speech import SpeechConfigurationError, transcribe_audio

router = APIRouter(prefix="/api/v1", tags=["meetings"])
settings = get_settings()


async def database_session(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AsyncSession]:
    async for session in get_session(settings):
        yield session


async def find_user_id(session: AsyncSession, subject: str) -> UUID:
    user_id = await session.scalar(select(User.id).where(User.external_id == subject))
    if user_id is None:
        raise HTTPException(status_code=403, detail="user is not a team member")
    return user_id


@router.post("/meetings", response_model=MeetingSummary, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Meeting:
    try:
        user_id = await find_user_id(session, principal.subject)
        membership = await session.scalar(
            select(TeamMember).where(
                TeamMember.team_id == payload.team_id,
                TeamMember.user_id == user_id,
            )
        )
        if membership is None:
            raise HTTPException(status_code=403, detail="user is not a team member")
        meeting = Meeting(
            team_id=payload.team_id,
            host_user_id=user_id,
            title=payload.title,
            scheduled_at=payload.scheduled_at,
            ai_intervention_level=payload.ai_intervention_level,
        )
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting
    except HTTPException:
        raise
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.get("/meetings", response_model=list[MeetingSummary])
async def list_meetings(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[Meeting]:
    query = (
        select(Meeting)
        .join(TeamMember, TeamMember.team_id == Meeting.team_id)
        .join(User, User.id == TeamMember.user_id)
        .where(User.external_id == principal.subject)
        .order_by(Meeting.created_at.desc())
    )
    try:
        return list((await session.scalars(query)).all())
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None


async def authorized_meeting(
    meeting_id: UUID, principal: Principal, session: AsyncSession, *, write: bool = False
) -> Meeting:
    query = (
        select(Meeting, TeamMember.role)
        .join(TeamMember, TeamMember.team_id == Meeting.team_id)
        .join(User, User.id == TeamMember.user_id)
        .where(Meeting.id == meeting_id, User.external_id == principal.subject)
    )
    row = (await session.execute(query)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="meeting not found")
    meeting, role = row
    if write and role not in {"owner", "admin"} and meeting.host_user_id != await find_user_id(
        session, principal.subject
    ):
        raise HTTPException(status_code=403, detail="insufficient permissions")
    return meeting


@router.get("/meetings/{meeting_id}", response_model=MeetingSummary)
async def get_meeting(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Meeting:
    try:
        return await authorized_meeting(meeting_id, principal, session)
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.get("/meetings/{meeting_id}/state", response_model=MeetingStateSnapshot)
async def get_meeting_state(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> MeetingStateSnapshot:
    """Return the current public snapshot for an authorized meeting participant."""
    try:
        await authorized_meeting(meeting_id, principal, session)
        snapshot = await session.scalar(
            select(MeetingState).where(MeetingState.meeting_id == meeting_id)
        )
        if snapshot is None:
            return MeetingStateSnapshot(
                meeting_id=meeting_id,
                state_version=0,
                state={},
                updated_at=None,
            )
        return MeetingStateSnapshot.model_validate(snapshot)
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.patch("/meetings/{meeting_id}/state", response_model=MeetingStateSnapshot)
async def update_meeting_state(
    meeting_id: UUID,
    payload: MeetingStateUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> MeetingStateSnapshot:
    """Apply a public state update only when the caller has the current version."""
    try:
        await authorized_meeting(meeting_id, principal, session)
        user_id = await find_user_id(session, principal.subject)
        snapshot = await session.scalar(
            select(MeetingState)
            .where(MeetingState.meeting_id == meeting_id)
            .with_for_update()
        )
        if snapshot is None:
            if payload.expected_state_version != 0:
                raise HTTPException(status_code=409, detail="meeting state version conflict")
            snapshot = MeetingState(
                meeting_id=meeting_id,
                state_version=1,
                state=payload.state,
                updated_by=user_id,
            )
            session.add(snapshot)
        else:
            if snapshot.state_version != payload.expected_state_version:
                raise HTTPException(status_code=409, detail="meeting state version conflict")
            snapshot.state_version += 1
            snapshot.state = payload.state
            snapshot.updated_by = user_id
        await session.commit()
        await session.refresh(snapshot)
        return MeetingStateSnapshot.model_validate(snapshot)
    except HTTPException:
        raise
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="meeting state version conflict") from None
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.patch("/meetings/{meeting_id}", response_model=MeetingSummary)
async def update_meeting(
    meeting_id: UUID,
    payload: MeetingUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Meeting:
    try:
        meeting = await authorized_meeting(meeting_id, principal, session, write=True)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(meeting, field, value)
        await session.commit()
        await session.refresh(meeting)
        return meeting
    except HTTPException:
        raise
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.post("/meetings/{meeting_id}/participants", status_code=status.HTTP_201_CREATED)
async def add_participant(
    meeting_id: UUID,
    payload: ParticipantAdd,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    try:
        meeting = await authorized_meeting(meeting_id, principal, session, write=True)
        member = await session.scalar(
            select(TeamMember).where(
                TeamMember.team_id == meeting.team_id, TeamMember.user_id == payload.user_id
            )
        )
        if member is None:
            raise HTTPException(status_code=400, detail="participant is not a team member")
        participant = MeetingParticipant(
            meeting_id=meeting_id, user_id=payload.user_id, role=payload.role
        )
        session.add(participant)
        await session.commit()
        return {
            "meeting_id": str(meeting_id),
            "user_id": str(payload.user_id),
            "role": payload.role,
        }
    except HTTPException:
        raise
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="participant already exists or request conflicts"
        ) from None


@router.post("/meetings/{meeting_id}/agenda", status_code=status.HTTP_201_CREATED)
async def add_agenda_item(
    meeting_id: UUID,
    payload: AgendaItemCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str | int]:
    try:
        meeting = await authorized_meeting(meeting_id, principal, session, write=True)
        item = AgendaItem(meeting_id=meeting.id, **payload.model_dump())
        session.add(item)
        await session.commit()
        return {"id": str(item.id), "meeting_id": str(meeting_id), "position": item.position}
    except HTTPException:
        raise
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="agenda position already exists") from None


@router.post("/meetings/{meeting_id}/start", response_model=MeetingSummary)
async def start_meeting(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Meeting:
    return await _transition_meeting(
        meeting_id, principal, session, "in_progress", {"draft", "scheduled"}
    )


@router.post("/meetings/{meeting_id}/end", response_model=MeetingSummary)
async def end_meeting(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Meeting:
    return await _transition_meeting(meeting_id, principal, session, "completed", {"in_progress"})


@router.post("/meetings/{meeting_id}/cancel", response_model=MeetingSummary)
async def cancel_meeting(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Meeting:
    return await _transition_meeting(
        meeting_id, principal, session, "cancelled", {"draft", "scheduled"}
    )


async def _transition_meeting(
    meeting_id: UUID,
    principal: Principal,
    session: AsyncSession,
    target: str,
    allowed: set[str],
) -> Meeting:
    try:
        meeting = await authorized_meeting(meeting_id, principal, session, write=True)
        if meeting.status not in allowed:
            raise HTTPException(status_code=409, detail="invalid meeting state transition")
        meeting.status = target
        await session.commit()
        await session.refresh(meeting)
        return meeting
    except HTTPException:
        raise
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.get("/meetings/{meeting_id}/participants")
async def list_participants(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, list[dict[str, str]]]:
    await authorized_meeting(meeting_id, principal, session)
    rows = (
        await session.execute(
            select(
                MeetingParticipant.user_id,
                MeetingParticipant.role,
                MeetingParticipant.attendance_status,
            )
            .where(MeetingParticipant.meeting_id == meeting_id)
        )
    ).all()
    return {
        "participants": [
            {"user_id": str(uid), "role": role, "attendance_status": state}
            for uid, role, state in rows
        ]
    }


@router.patch("/meetings/{meeting_id}/participants/{user_id}")
async def update_participant(
    meeting_id: UUID,
    user_id: UUID,
    payload: ParticipantUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    await authorized_meeting(meeting_id, principal, session, write=True)
    participant = await session.scalar(select(MeetingParticipant).where(
        MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == user_id
    ))
    if participant is None:
        raise HTTPException(status_code=404, detail="participant not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(participant, field, value)
    await session.commit()
    return {
        "user_id": str(user_id),
        "role": participant.role,
        "attendance_status": participant.attendance_status,
    }


@router.delete(
    "/meetings/{meeting_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_participant(
    meeting_id: UUID, user_id: UUID, principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    await authorized_meeting(meeting_id, principal, session, write=True)
    participant = await session.scalar(select(MeetingParticipant).where(
        MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == user_id
    ))
    if participant is None:
        raise HTTPException(status_code=404, detail="participant not found")
    await session.delete(participant)
    await session.commit()


@router.get("/meetings/{meeting_id}/agenda")
async def list_agenda(
    meeting_id: UUID, principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, list[dict[str, object]]]:
    await authorized_meeting(meeting_id, principal, session)
    items = (await session.scalars(select(AgendaItem).where(
        AgendaItem.meeting_id == meeting_id
    ).order_by(AgendaItem.position))).all()
    return {"items": [{"id": str(i.id), "position": i.position, "title": i.title,
                        "description": i.description, "status": i.status} for i in items]}


@router.patch("/meetings/{meeting_id}/agenda/{item_id}")
async def update_agenda_item(
    meeting_id: UUID, item_id: UUID, payload: AgendaItemUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    await authorized_meeting(meeting_id, principal, session, write=True)
    item = await session.scalar(select(AgendaItem).where(
        AgendaItem.id == item_id, AgendaItem.meeting_id == meeting_id
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="agenda item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await session.commit()
    return {"id": str(item.id), "position": item.position, "title": item.title,
            "description": item.description, "status": item.status}


@router.delete("/meetings/{meeting_id}/agenda/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agenda_item(
    meeting_id: UUID, item_id: UUID, principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    await authorized_meeting(meeting_id, principal, session, write=True)
    item = await session.scalar(select(AgendaItem).where(
        AgendaItem.id == item_id, AgendaItem.meeting_id == meeting_id
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="agenda item not found")
    await session.delete(item)
    await session.commit()


@router.post("/meetings/{meeting_id}/transcription", response_model=TranscriptionResponse)
async def transcribe_meeting_audio(
    meeting_id: UUID,
    file: UploadFile = File(...),
    speaker_label: str = Form(default="unknown", max_length=255),
    speaker_user_id: UUID | None = Form(default=None),
    started_at: datetime | None = Form(default=None),
    ended_at: datetime | None = Form(default=None),
    language: str | None = Form(default="zh", max_length=16),
    idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key", max_length=128),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> TranscriptionResponse:
    await authorized_meeting(meeting_id, principal, session)
    if idempotency_key:
        existing = await session.scalar(
            select(Transcript).where(
                Transcript.meeting_id == meeting_id,
                Transcript.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return TranscriptionResponse(
                meeting_id=meeting_id,
                transcript_id=existing.id,
                sequence=existing.sequence,
                text=existing.text,
                model=settings.groq_stt_model,
            )
    if speaker_user_id is not None:
        member = await session.scalar(
            select(TeamMember)
            .join(Meeting, Meeting.team_id == TeamMember.team_id)
            .where(Meeting.id == meeting_id, TeamMember.user_id == speaker_user_id)
        )
        if member is None:
            raise HTTPException(status_code=400, detail="speaker is not a meeting team member")
    content = await file.read(25_000_001)
    if len(content) > 25_000_000:
        raise HTTPException(status_code=413, detail="audio file is too large")
    try:
        text = await transcribe_audio(
            file.filename or "audio.webm",
            content,
            file.content_type or "application/octet-stream",
            settings,
            language=language,
        )
    except SpeechConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="speech provider unavailable") from None
    latest_sequence = await session.scalar(
        select(func.max(Transcript.sequence)).where(Transcript.meeting_id == meeting_id)
    )
    sequence = int(latest_sequence or 0) + 1
    now = datetime.now(UTC)
    segment = Transcript(
        meeting_id=meeting_id,
        speaker_user_id=speaker_user_id,
        speaker_label=speaker_label.strip() or "unknown",
        sequence=sequence,
        started_at=started_at or now,
        ended_at=ended_at or now,
        text=text,
        source="groq",
        idempotency_key=idempotency_key,
    )
    try:
        for attempt in range(2):
            session.add(segment)
            try:
                await session.commit()
                await session.refresh(segment)
                break
            except IntegrityError:
                await session.rollback()
                if attempt == 1:
                    raise
                latest_sequence = await session.scalar(
                    select(func.max(Transcript.sequence)).where(Transcript.meeting_id == meeting_id)
                )
                segment = Transcript(
                    meeting_id=meeting_id,
                    speaker_user_id=speaker_user_id,
                    speaker_label=speaker_label.strip() or "unknown",
                    sequence=int(latest_sequence or 0) + 1,
                    started_at=started_at or now,
                    ended_at=ended_at or now,
                    text=text,
                    source="groq",
                    idempotency_key=idempotency_key,
                )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="transcript could not be saved") from None
    return TranscriptionResponse(
        meeting_id=meeting_id,
        transcript_id=segment.id,
        sequence=segment.sequence,
        text=text,
        model=settings.groq_stt_model,
    )


@router.post("/meetings/{meeting_id}/transcripts/backup", status_code=status.HTTP_201_CREATED)
async def backup_meeting_transcripts(
    meeting_id: UUID,
    payload: TranscriptBackupRequest,
    webhook_secret: str | None = Header(default=None, alias="X-Meeting-BaaS-Secret"),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    if (
        not settings.meeting_baas_webhook_secret
        or webhook_secret != settings.meeting_baas_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="invalid webhook secret")
    meeting = await session.scalar(select(Meeting).where(Meeting.id == meeting_id))
    if meeting is None:
        raise HTTPException(status_code=404, detail="meeting not found")
    latest = await session.scalar(
        select(func.max(Transcript.sequence)).where(Transcript.meeting_id == meeting_id)
    )
    segments = []
    for index, item in enumerate(payload.segments, start=int(latest or 0) + 1):
        segments.append(
            Transcript(
                meeting_id=meeting_id,
                speaker_user_id=item.speaker_user_id,
                speaker_label=item.speaker_label,
                sequence=index,
                started_at=item.started_at,
                ended_at=item.ended_at,
                text=item.text,
                source="meeting_baas",
                confidence=item.confidence,
            )
        )
    session.add_all(segments)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="transcript sequence conflict") from None
    return {"meeting_id": str(meeting_id), "created": len(segments)}
