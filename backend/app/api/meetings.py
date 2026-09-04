from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import Meeting, TeamMember, User
from app.schemas.meeting import MeetingCreate, MeetingSummary

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
