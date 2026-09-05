from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.models import PreparationMessage
from app.schemas.meeting import PreparationMessageCreate, PreparationMessageSummary
from app.services.llm import LLMConfigurationError, LLMProviderError, complete_preparation

router = APIRouter(prefix="/api/v1", tags=["preparation"])


@router.get(
    "/meetings/{meeting_id}/preparation/messages", response_model=list[PreparationMessageSummary]
)
async def list_preparation_messages(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
):
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    return list(
        (
            await session.scalars(
                select(PreparationMessage)
                .where(
                    PreparationMessage.meeting_id == meeting_id,
                    PreparationMessage.user_id == user_id,
                )
                .order_by(PreparationMessage.created_at)
            )
        ).all()
    )


@router.post(
    "/meetings/{meeting_id}/preparation/messages",
    response_model=list[PreparationMessageSummary],
    status_code=status.HTTP_201_CREATED,
)
async def create_preparation_message(
    meeting_id: UUID,
    payload: PreparationMessageCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
    settings: Settings = Depends(get_settings),
):
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    history = list(
        (
            await session.scalars(
                select(PreparationMessage)
                .where(
                    PreparationMessage.meeting_id == meeting_id,
                    PreparationMessage.user_id == user_id,
                )
                .order_by(PreparationMessage.created_at)
            )
        ).all()
    )
    user_message = PreparationMessage(
        meeting_id=meeting_id, user_id=user_id, role="user", content=payload.content
    )
    session.add(user_message)
    try:
        answer = await complete_preparation(
            [{"role": item.role, "content": item.content} for item in history]
            + [{"role": "user", "content": payload.content}],
            settings,
        )
    except LLMConfigurationError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError:
        await session.rollback()
        raise HTTPException(status_code=502, detail="LLM provider unavailable") from None
    assistant_message = PreparationMessage(
        meeting_id=meeting_id, user_id=user_id, role="assistant", content=answer
    )
    session.add(assistant_message)
    try:
        await session.commit()
        await session.refresh(user_message)
        await session.refresh(assistant_message)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return [user_message, assistant_message]
