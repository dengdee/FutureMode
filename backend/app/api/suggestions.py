from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.models import AISuggestion, SuggestionVote
from app.schemas.meeting import SuggestionStatusUpdate, SuggestionSummary, SuggestionVoteCreate

router = APIRouter(prefix="/api/v1", tags=["suggestions"])


@router.get("/meetings/{meeting_id}/suggestions", response_model=list[SuggestionSummary])
async def list_suggestions(
    meeting_id: UUID, principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[AISuggestion]:
    await authorized_meeting(meeting_id, principal, session)
    try:
        return list((await session.scalars(select(AISuggestion).where(
            AISuggestion.meeting_id == meeting_id
        ).order_by(AISuggestion.created_at))).all())
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.post("/meetings/{meeting_id}/suggestions/{suggestion_id}/vote")
async def vote_suggestion(
    meeting_id: UUID, suggestion_id: UUID, payload: SuggestionVoteCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    meeting = await authorized_meeting(meeting_id, principal, session)
    suggestion = await session.scalar(select(AISuggestion).where(
        AISuggestion.id == suggestion_id, AISuggestion.meeting_id == meeting.id
    ))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    user_id = await find_user_id(session, principal.subject)
    vote = await session.scalar(select(SuggestionVote).where(
        SuggestionVote.suggestion_id == suggestion_id, SuggestionVote.user_id == user_id
    ))
    if vote is None:
        vote = SuggestionVote(suggestion_id=suggestion_id, user_id=user_id, vote=payload.vote)
        session.add(vote)
    else:
        vote.vote = payload.vote
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {"suggestion_id": str(suggestion_id), "vote": payload.vote}


@router.patch(
    "/meetings/{meeting_id}/suggestions/{suggestion_id}", response_model=SuggestionSummary
)
async def update_suggestion_status(
    meeting_id: UUID,
    suggestion_id: UUID,
    payload: SuggestionStatusUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> AISuggestion:
    meeting = await authorized_meeting(meeting_id, principal, session, write=True)
    suggestion = await session.scalar(select(AISuggestion).where(
        AISuggestion.id == suggestion_id, AISuggestion.meeting_id == meeting.id
    ))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    suggestion.status = payload.status
    try:
        await session.commit()
        await session.refresh(suggestion)
        return suggestion
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.get("/meetings/{meeting_id}/suggestions/{suggestion_id}/votes")
async def list_suggestion_votes(
    meeting_id: UUID,
    suggestion_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, list[dict[str, str]]]:
    await authorized_meeting(meeting_id, principal, session)
    suggestion = await session.scalar(select(AISuggestion).where(
        AISuggestion.id == suggestion_id, AISuggestion.meeting_id == meeting_id
    ))
    if suggestion is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    rows = (await session.execute(select(SuggestionVote.user_id, SuggestionVote.vote).where(
        SuggestionVote.suggestion_id == suggestion_id
    ))).all()
    return {"votes": [{"user_id": str(user_id), "vote": vote} for user_id, vote in rows]}
