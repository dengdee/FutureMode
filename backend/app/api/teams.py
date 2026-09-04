from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import Team, TeamMember, User

router = APIRouter(prefix="/api/v1", tags=["teams"])


async def database_session(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AsyncSession]:
    async for session in get_session(settings):
        yield session


@router.get("/teams")
async def list_teams(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, list[dict[str, str]]]:
    query = (
        select(Team.id, Team.name, TeamMember.role)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .join(User, User.id == TeamMember.user_id)
        .where(User.external_id == principal.subject)
        .order_by(Team.name)
    )
    try:
        rows = (await session.execute(query)).all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {
        "teams": [{"id": str(team_id), "name": name, "role": role} for team_id, name, role in rows]
    }
