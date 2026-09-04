from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.models import DelegateProfile
from app.schemas.meeting import DelegateProfileCreate

router = APIRouter(prefix="/api/v1", tags=["delegates"])


@router.post("/meetings/{meeting_id}/delegates", status_code=status.HTTP_201_CREATED)
async def create_delegate(
    meeting_id: UUID, payload: DelegateProfileCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    profile = DelegateProfile(meeting_id=meeting_id, user_id=user_id, **payload.model_dump())
    session.add(profile)
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {"id": str(profile.id), "meeting_id": str(meeting_id), "status": profile.status}


@router.get("/meetings/{meeting_id}/delegates")
async def list_delegates(
    meeting_id: UUID, principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, object]]:
    await authorized_meeting(meeting_id, principal, session)
    profiles = (await session.scalars(select(DelegateProfile).where(
        DelegateProfile.meeting_id == meeting_id
    ))).all()
    return [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "stance": p.stance,
            "constraints": p.constraints,
            "must_raise": p.must_raise,
            "status": p.status,
        }
        for p in profiles
    ]
