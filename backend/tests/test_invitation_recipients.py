import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.api.teams import create_invitation
from app.auth.principal import Principal
from app.models import Team, TeamInvitation, TeamMember, User
from app.schemas.team import InvitationCreate


def setup_creation(role="admin", existing=None, already_member=False):
    actor = User(id=uuid4(), external_id="actor")
    recipient = User(
        id=uuid4(), external_id="recipient", display_name="小明", email="person@example.com"
    )
    team = Team(id=uuid4(), name="測試")
    db = MagicMock()
    db.scalar = AsyncMock(side_effect=[actor, TeamMember(role=role), team, recipient,
                                      TeamMember() if already_member else None, existing])
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db, recipient, team


def test_email_is_required_and_normalized():
    assert InvitationCreate(email=" Person@Example.com ").email == "person@example.com"
    with pytest.raises(ValidationError):
        InvitationCreate()


def test_admin_invites_selected_account_without_email_claims():
    db, recipient, team = setup_creation()
    result = asyncio.run(create_invitation(team.id, InvitationCreate(
        email="person@example.com"), Principal("actor", {}), db))
    assert result.recipient_user_id == recipient.id
    assert result.recipient_name == "小明"
    assert result.email is None
    assert result.role == "member"
    db.commit.assert_awaited_once()


def test_non_admin_cannot_invite():
    db, recipient, team = setup_creation(role="member")
    with pytest.raises(HTTPException) as error:
        asyncio.run(create_invitation(team.id, InvitationCreate(
            email="person@example.com"), Principal("actor", {}), db))
    assert error.value.status_code == 403
    db.scalar.assert_awaited()
    db.add.assert_not_called()


@pytest.mark.parametrize("missing,expected", [(True, 404), (False, 409)])
def test_recipient_must_exist_and_not_already_be_member(missing, expected, monkeypatch):
    db, recipient, team = setup_creation(already_member=True)
    if missing:
        db.scalar.side_effect = [
            User(id=uuid4(), external_id="actor"), TeamMember(role="admin"), team, None
        ]
        async def no_neon_user(*_args):
            return None
        monkeypatch.setattr("app.api.teams.find_neon_auth_user", no_neon_user)
    with pytest.raises(HTTPException) as error:
        asyncio.run(create_invitation(team.id, InvitationCreate(
            email="person@example.com"), Principal("actor", {}), db))
    assert error.value.status_code == expected
    db.add.assert_not_called()


def test_registered_neon_auth_user_is_synced_before_invitation(monkeypatch):
    db, _recipient, team = setup_creation()
    db.scalar.side_effect = [
        User(id=uuid4(), external_id="actor"), TeamMember(role="admin"), team, None, None, None
    ]
    db.flush = AsyncMock()

    async def neon_user(*_args):
        return {"external_id": "neon-user", "email": "person@example.com", "display_name": "小明"}

    monkeypatch.setattr("app.api.teams.find_neon_auth_user", neon_user)
    result = asyncio.run(create_invitation(team.id, InvitationCreate(
        email="person@example.com"), Principal("actor", {}), db))

    synced_user = db.add.call_args_list[0].args[0]
    assert isinstance(synced_user, User)
    assert synced_user.external_id == "neon-user"
    assert synced_user.email == "person@example.com"
    assert result.recipient_user_id == synced_user.id
    db.flush.assert_awaited_once()


def test_duplicate_pending_recipient_returns_existing_invitation():
    existing = TeamInvitation(id=uuid4(), status="pending", role="member")
    db, recipient, team = setup_creation(existing=existing)
    result = asyncio.run(create_invitation(team.id, InvitationCreate(
        email="person@example.com"), Principal("actor", {}), db))
    assert result is existing
    db.add.assert_not_called()
    query = db.scalar.call_args.args[0].compile(dialect=postgresql.dialect())
    assert "team_invitations.recipient_user_id =" in str(query)
    assert recipient.id in query.params.values()
