from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.models import ActionItem, ConsensusFeedback, ConsensusVersion
from app.schemas.meeting import (
    ActionItemCreate,
    ActionItemUpdate,
    ConsensusCreate,
    ConsensusFeedbackCreate,
)

router = APIRouter(prefix="/api/v1", tags=["consensus"])


@router.post("/meetings/{meeting_id}/consensus", status_code=status.HTTP_201_CREATED)
async def create_consensus(
    meeting_id: UUID,
    payload: ConsensusCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    await authorized_meeting(meeting_id, principal, session, write=True)
    user_id = await find_user_id(session, principal.subject)
    current = await session.scalar(
        select(func.coalesce(func.max(ConsensusVersion.version), 0)).where(
            ConsensusVersion.meeting_id == meeting_id
        )
    )
    version = ConsensusVersion(
        meeting_id=meeting_id, version=current + 1, content=payload.content, created_by=user_id
    )
    session.add(version)
    await session.commit()
    return {
        "id": str(version.id),
        "meeting_id": str(meeting_id),
        "version": version.version,
        "status": version.status,
    }


@router.get("/meetings/{meeting_id}/consensus")
async def list_consensus(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, object]]:
    await authorized_meeting(meeting_id, principal, session)
    rows = (
        await session.scalars(
            select(ConsensusVersion)
            .where(ConsensusVersion.meeting_id == meeting_id)
            .order_by(ConsensusVersion.version)
        )
    ).all()
    return [
        {"id": str(v.id), "version": v.version, "content": v.content, "status": v.status}
        for v in rows
    ]


@router.post("/meetings/{meeting_id}/consensus/{version_id}/feedback")
async def feedback_consensus(
    meeting_id: UUID,
    version_id: UUID,
    payload: ConsensusFeedbackCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    await authorized_meeting(meeting_id, principal, session)
    version = await session.scalar(
        select(ConsensusVersion).where(
            ConsensusVersion.id == version_id, ConsensusVersion.meeting_id == meeting_id
        )
    )
    if version is None:
        raise HTTPException(status_code=404, detail="consensus version not found")
    user_id = await find_user_id(session, principal.subject)
    feedback = await session.scalar(
        select(ConsensusFeedback).where(
            ConsensusFeedback.version_id == version_id, ConsensusFeedback.user_id == user_id
        )
    )
    if feedback is None:
        feedback = ConsensusFeedback(version_id=version_id, user_id=user_id, **payload.model_dump())
        session.add(feedback)
    else:
        feedback.decision, feedback.comment = payload.decision, payload.comment
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {"version_id": str(version_id), "decision": feedback.decision}


@router.post("/meetings/{meeting_id}/action-items", status_code=status.HTTP_201_CREATED)
async def create_action_item(
    meeting_id: UUID,
    payload: ActionItemCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    await authorized_meeting(meeting_id, principal, session, write=True)
    item = ActionItem(meeting_id=meeting_id, **payload.model_dump())
    session.add(item)
    await session.commit()
    return {
        "id": str(item.id),
        "meeting_id": str(meeting_id),
        "title": item.title,
        "status": item.status,
    }


@router.get("/meetings/{meeting_id}/action-items")
async def list_action_items(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, object]]:
    await authorized_meeting(meeting_id, principal, session)
    rows = (
        await session.scalars(select(ActionItem).where(ActionItem.meeting_id == meeting_id))
    ).all()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "assignee_user_id": str(i.assignee_user_id) if i.assignee_user_id else None,
            "due_date": i.due_date,
            "status": i.status,
        }
        for i in rows
    ]


@router.get("/meetings/{meeting_id}/consensus/{version_id}/feedback")
async def list_feedback(
    meeting_id: UUID,
    version_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, str | None]]:
    await authorized_meeting(meeting_id, principal, session)
    version = await session.scalar(
        select(ConsensusVersion).where(
            ConsensusVersion.id == version_id, ConsensusVersion.meeting_id == meeting_id
        )
    )
    if version is None:
        raise HTTPException(status_code=404, detail="consensus version not found")
    rows = (
        await session.scalars(
            select(ConsensusFeedback).where(ConsensusFeedback.version_id == version_id)
        )
    ).all()
    return [{"user_id": str(f.user_id), "decision": f.decision, "comment": f.comment} for f in rows]


@router.post("/meetings/{meeting_id}/consensus/{version_id}/confirm")
async def confirm_consensus(
    meeting_id: UUID,
    version_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    await authorized_meeting(meeting_id, principal, session, write=True)
    version = await session.scalar(
        select(ConsensusVersion).where(
            ConsensusVersion.id == version_id, ConsensusVersion.meeting_id == meeting_id
        )
    )
    if version is None:
        raise HTTPException(status_code=404, detail="consensus version not found")
    feedback = (
        await session.scalars(
            select(ConsensusFeedback).where(ConsensusFeedback.version_id == version_id)
        )
    ).all()
    if not feedback or any(item.decision != "agree" for item in feedback):
        raise HTTPException(status_code=409, detail="consensus requires all feedback to agree")
    version.status = "confirmed"
    await session.commit()
    return {"version_id": str(version_id), "status": version.status}


@router.patch("/meetings/{meeting_id}/action-items/{item_id}")
async def update_action_item(
    meeting_id: UUID,
    item_id: UUID,
    payload: ActionItemUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    await authorized_meeting(meeting_id, principal, session, write=True)
    item = await session.scalar(
        select(ActionItem).where(ActionItem.id == item_id, ActionItem.meeting_id == meeting_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="action item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await session.commit()
    return {"id": str(item.id), "title": item.title, "status": item.status}


@router.delete("/meetings/{meeting_id}/action-items/{item_id}", status_code=204)
async def delete_action_item(
    meeting_id: UUID,
    item_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    await authorized_meeting(meeting_id, principal, session, write=True)
    item = await session.scalar(
        select(ActionItem).where(ActionItem.id == item_id, ActionItem.meeting_id == meeting_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="action item not found")
    await session.delete(item)
    await session.commit()
