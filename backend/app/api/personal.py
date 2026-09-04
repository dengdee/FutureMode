from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.models import PersonalAgentMessage, PublicContribution
from app.schemas.meeting import ContributionPublish, PersonalMessageCreate, PersonalMessageSummary

router = APIRouter(prefix="/api/v1", tags=["personal-agent"])


@router.post(
    "/meetings/{meeting_id}/personal/messages",
    response_model=PersonalMessageSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_personal_message(
    meeting_id: UUID,
    payload: PersonalMessageCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> PersonalAgentMessage:
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    message = PersonalAgentMessage(
        meeting_id=meeting_id, user_id=user_id, role="user", content=payload.content
    )
    session.add(message)
    try:
        await session.commit()
        await session.refresh(message)
        return message
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.get("/meetings/{meeting_id}/personal/messages", response_model=list[PersonalMessageSummary])
async def list_personal_messages(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[PersonalAgentMessage]:
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    try:
        return list((await session.scalars(select(PersonalAgentMessage).where(
            PersonalAgentMessage.meeting_id == meeting_id,
            PersonalAgentMessage.user_id == user_id,
        ).order_by(PersonalAgentMessage.created_at))).all())
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None


@router.post("/meetings/{meeting_id}/personal/contributions/preview")
async def preview_contribution(
    meeting_id: UUID, payload: ContributionPublish,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    await authorized_meeting(meeting_id, principal, session)
    return {
        "content": payload.content,
        "source_message_id": payload.source_message_id,
        "requires_confirmation": True,
    }


@router.post(
    "/meetings/{meeting_id}/personal/contributions/publish",
    status_code=status.HTTP_201_CREATED,
)
async def publish_contribution(
    meeting_id: UUID, payload: ContributionPublish,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    if payload.source_message_id is not None:
        source = await session.scalar(select(PersonalAgentMessage).where(
            PersonalAgentMessage.id == payload.source_message_id,
            PersonalAgentMessage.meeting_id == meeting_id,
            PersonalAgentMessage.user_id == user_id,
        ))
        if source is None:
            raise HTTPException(status_code=404, detail="source message not found")
    contribution = PublicContribution(
        meeting_id=meeting_id, user_id=user_id, content=payload.content,
        source_message_id=payload.source_message_id,
    )
    session.add(contribution)
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {
        "id": str(contribution.id),
        "meeting_id": str(meeting_id),
        "status": contribution.status,
    }
