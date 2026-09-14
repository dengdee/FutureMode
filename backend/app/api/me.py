from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.teams import principal_name
from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import User
from app.schemas.team import ProfileUpdate

router = APIRouter(prefix="/api/v1", tags=["identity"])


async def database_session(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AsyncSession]:
    async for session in get_session(settings):
        yield session


@router.get("/me")
async def get_me(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    """Return the canonical local profile for the authenticated subject."""
    user = await session.scalar(select(User).where(User.external_id == principal.subject))
    claim_name = principal_name(principal)
    if user is None:
        user = User(
            external_id=principal.subject,
            display_name=claim_name,
            email=principal.claims.get("email")
            if isinstance(principal.claims.get("email"), str)
            else None,
        )
        session.add(user)
    elif not user.display_name and claim_name:
        user.display_name = claim_name
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {
        "id": principal.subject,
        "display_name": user.display_name,
        "email": user.email,
        "claims": principal.claims,
    }


@router.patch("/me")
async def update_me(
    payload: ProfileUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    user = await session.scalar(select(User).where(User.external_id == principal.subject))
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="profile update conflicts") from None
    return {"id": principal.subject, "display_name": user.display_name, "email": user.email}
