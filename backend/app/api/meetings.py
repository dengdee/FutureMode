from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import AgendaItem, Meeting, MeetingParticipant, TeamMember, User
from app.schemas.meeting import (
    AgendaItemCreate,
    MeetingCreate,
    MeetingSummary,
    MeetingUpdate,
    ParticipantAdd,
)

router = APIRouter(prefix="/api/v1", tags=["meetings"])


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
