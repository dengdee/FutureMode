from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import Team, TeamMember, User
from app.schemas.team import RoleUpdate, TeamCreate

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


@router.post("/teams", status_code=201)
async def create_team(
    payload: TeamCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    user = await session.scalar(select(User).where(User.external_id == principal.subject))
    if user is None:
        raise HTTPException(status_code=403, detail="user is not provisioned")
    team = Team(name=payload.name)
    session.add(team)
    await session.flush()
    session.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
    await session.commit()
    return {"id": str(team.id), "name": team.name, "role": "owner"}


@router.patch("/teams/{team_id}/members/{user_id}")
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    payload: RoleUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    actor_membership = await session.scalar(select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
    ))
    if actor_membership is None or actor_membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="insufficient permissions")
    membership = await session.scalar(select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == user_id
    ))
    if membership is None:
        raise HTTPException(status_code=404, detail="team member not found")
    membership.role = payload.role
    await session.commit()
    return {"team_id": str(team_id), "user_id": str(user_id), "role": membership.role}


@router.delete("/teams/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
    team_id: UUID,
    user_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    actor_membership = await session.scalar(select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
    ))
    if actor_membership is None or actor_membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="insufficient permissions")
    membership = await session.scalar(select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == user_id
    ))
    if membership is None:
        raise HTTPException(status_code=404, detail="team member not found")
    await session.delete(membership)
    await session.commit()


@router.get("/teams/{team_id}/members")
async def list_team_members(
    team_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, list[dict[str, str]]]:
    query = (
        select(User.external_id, User.display_name, TeamMember.role)
        .join(TeamMember, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
        .where(
            TeamMember.team_id.in_(
                select(TeamMember.team_id)
                .join(User, User.id == TeamMember.user_id)
                .where(User.external_id == principal.subject)
            )
        )
    )
    try:
        rows = (await session.execute(query)).all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {
        "members": [
            {"external_id": external_id, "display_name": display_name or "", "role": role}
            for external_id, display_name, role in rows
        ]
    }
