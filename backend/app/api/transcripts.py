from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session
from app.auth.principal import Principal, get_current_principal
from app.models import Transcript
from app.schemas.meeting import TranscriptCreate, TranscriptSummary

router = APIRouter(prefix="/api/v1", tags=["transcripts"])


@router.post(
    "/meetings/{meeting_id}/transcripts",
    response_model=TranscriptSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_transcript(
    meeting_id: UUID,
    payload: TranscriptCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> Transcript:
    await authorized_meeting(meeting_id, principal, session)
    segment = Transcript(meeting_id=meeting_id, **payload.model_dump())
    session.add(segment)
    try:
        await session.commit()
        await session.refresh(segment)
        return segment
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="transcript sequence already exists") from None
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.get("/meetings/{meeting_id}/transcripts", response_model=list[TranscriptSummary])
async def list_transcripts(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[Transcript]:
    await authorized_meeting(meeting_id, principal, session)
    try:
        return list(
            (
                await session.scalars(
                    select(Transcript)
                    .where(Transcript.meeting_id == meeting_id)
                    .order_by(Transcript.sequence)
                )
            ).all()
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None
