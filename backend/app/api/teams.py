from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import Team, TeamInvitation, TeamMember, User
from app.schemas.team import InvitationCreate, InvitationSummary, RoleUpdate, TeamCreate, TeamUpdate

router = APIRouter(prefix="/api/v1", tags=["teams"])


def principal_name(principal: Principal) -> str | None:
    name = principal.claims.get("name") or principal.claims.get("display_name")
    return name.strip()[:255] if isinstance(name, str) and name.strip() else None


def invitation_email(principal: Principal) -> str:
    claims = principal.claims
    email = claims.get("email")
    # Authentication identifies the account; invitation redemption also requires email ownership.
    verification_values = (claims.get("email_verified"), claims.get("emailVerified"))
    verified = (
        any(value is True for value in verification_values)
    )
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(status_code=403, detail="invitation_identity_email_missing")
    if not verified:
        raise HTTPException(status_code=403, detail="invitation_identity_email_unverified")
    return email.strip().lower()


async def database_session(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AsyncSession]:
    async for session in get_session(settings):
        yield session


@router.patch("/teams/{team_id}")
async def update_team(
    team_id: UUID,
    payload: TeamUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    membership = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
        )
    )
    if membership is None or membership.role != "admin":
        raise HTTPException(status_code=403, detail="insufficient permissions")
    team = await session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="team not found")
    team.name = payload.name
    await session.commit()
    return {"id": str(team.id), "name": team.name}


@router.delete("/teams/{team_id}", status_code=204)
async def delete_team(
    team_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    membership = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == (actor.id if actor else None),
            TeamMember.role == "admin",
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="admin permission required")
    team = await session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="team not found")
    await session.delete(team)
    await session.commit()


@router.post("/teams/{team_id}/invitations", response_model=InvitationSummary, status_code=201)
async def create_invitation(
    team_id: UUID,
    payload: InvitationCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> TeamInvitation:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    membership = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
        )
    )
    if membership is None or membership.role != "admin":
        raise HTTPException(status_code=403, detail="insufficient permissions")
    # Serialize invitations for a team so retries cannot create duplicate pending rows.
    await session.scalar(select(Team).where(Team.id == team_id).with_for_update())
    existing = await session.scalar(
        select(TeamInvitation).where(
            TeamInvitation.team_id == team_id,
            func.lower(TeamInvitation.email) == payload.email.strip().lower(),
            TeamInvitation.status == "pending",
        )
    )
    if existing is not None:
        await session.commit()
        return existing
    invitation = TeamInvitation(
        team_id=team_id, email=payload.email.strip().lower(), role=payload.role, invited_by=actor.id
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation


@router.get("/teams/{team_id}/invitations", response_model=list[InvitationSummary])
async def list_invitations(
    team_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[TeamInvitation]:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    membership = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
        )
    )
    if membership is None or membership.role != "admin":
        raise HTTPException(status_code=403, detail="insufficient permissions")
    return list(
        (
            await session.scalars(
                select(TeamInvitation)
                .where(TeamInvitation.team_id == team_id)
                .order_by(TeamInvitation.created_at.desc())
            )
        ).all()
    )


@router.delete("/teams/{team_id}/invitations/{invitation_id}", status_code=204)
async def cancel_invitation(
    team_id: UUID,
    invitation_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    invitations = await list_invitations(team_id, principal, session)
    invitation = next((item for item in invitations if item.id == invitation_id), None)
    if invitation is None:
        raise HTTPException(status_code=404, detail="invitation not found")
    invitation = await session.scalar(select(TeamInvitation).where(
        TeamInvitation.id == invitation_id,
    ).with_for_update().execution_options(populate_existing=True))
    if invitation is None:
        raise HTTPException(status_code=404, detail="invitation not found")
    if invitation.status == "cancelled":
        return
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="invitation is no longer pending")
    invitation.status = "cancelled"
    await session.commit()


@router.get("/me/invitations")
async def my_invitations(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, str]]:
    name = principal_name(principal)
    values = {"external_id": principal.subject, "display_name": name}
    statement = insert(User).values(**values)
    if name:
        statement = statement.on_conflict_do_update(
            index_elements=[User.external_id],
            set_={"display_name": func.coalesce(
                func.nullif(User.display_name, ""), statement.excluded.display_name,
            )},
        )
    else:
        statement = statement.on_conflict_do_nothing(index_elements=[User.external_id])
    await session.execute(statement)
    await session.commit()
    email = invitation_email(principal)
    rows = (await session.execute(
        select(TeamInvitation, Team.name).join(Team, Team.id == TeamInvitation.team_id)
        .where(func.lower(TeamInvitation.email) == email, TeamInvitation.status == "pending")
        .order_by(TeamInvitation.created_at.desc())
    )).all()
    return [dict(id=str(invite.id), team_id=str(invite.team_id), team_name=name,
                 role=invite.role, status=invite.status) for invite, name in rows]


@router.post("/me/invitations/{invitation_id}/{action}")
async def respond_invitation(
    invitation_id: UUID,
    action: str,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    if action not in {"accept", "decline"}:
        raise HTTPException(status_code=422, detail="action must be accept or decline")
    email = invitation_email(principal)
    invite = await session.scalar(select(TeamInvitation).where(
        TeamInvitation.id == invitation_id, func.lower(TeamInvitation.email) == email,
    ).with_for_update())
    if invite is None:
        raise HTTPException(status_code=404, detail="invitation not found")
    status = "accepted" if action == "accept" else "declined"
    if invite.status == status:
        return {"status": status, "team_id": str(invite.team_id)}
    if invite.status != "pending":
        raise HTTPException(status_code=409, detail="invitation is no longer pending")
    if invite.role not in {"admin", "member"}:
        raise HTTPException(status_code=409, detail="invitation role is invalid")
    if action == "accept":
        await session.execute(insert(User).values(
            external_id=principal.subject, display_name=principal_name(principal),
        ).on_conflict_do_nothing(index_elements=[User.external_id]))
        user_id = await session.scalar(select(User.id).where(User.external_id == principal.subject))
        await session.execute(insert(TeamMember).values(
            team_id=invite.team_id, user_id=user_id, role=invite.role,
        ).on_conflict_do_nothing(index_elements=[TeamMember.team_id, TeamMember.user_id]))
    invite.status = status
    await session.commit()
    return {"status": status, "team_id": str(invite.team_id)}


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
    try:
        # Only provision the verified subject. Never identify accounts by client-provided email.
        # Concurrent first requests share the unique external_id; existing profiles stay intact.
        await session.execute(
            insert(User).values(
                external_id=principal.subject, display_name=principal_name(principal),
            )
            .on_conflict_do_nothing(index_elements=[User.external_id])
        )
        user_id = await session.scalar(select(User.id).where(User.external_id == principal.subject))
        if user_id is None:
            raise SQLAlchemyError("user provisioning failed")
        team = Team(name=payload.name)
        session.add(team)
        await session.flush()
        session.add(TeamMember(team_id=team.id, user_id=user_id, role="admin"))
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return {"id": str(team.id), "name": team.name, "role": "admin"}


@router.patch("/teams/{team_id}/members/{user_id}")
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    payload: RoleUpdate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    actor = await session.scalar(select(User).where(User.external_id == principal.subject))
    actor_membership = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
        )
    )
    if actor_membership is None or actor_membership.role != "admin":
        raise HTTPException(status_code=403, detail="insufficient permissions")
    membership = await session.scalar(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
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
    actor_membership = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == (actor.id if actor else None)
        )
    )
    if actor_membership is None or actor_membership.role != "admin":
        raise HTTPException(status_code=403, detail="insufficient permissions")
    membership = await session.scalar(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
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
        select(User.id, User.external_id, User.display_name, TeamMember.role)
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
            {
                "user_id": str(user_id),
                "external_id": external_id,
                "display_name": display_name or "未設定名稱的成員",
                "role": role,
            }
            for user_id, external_id, display_name, role in rows
        ]
    }
