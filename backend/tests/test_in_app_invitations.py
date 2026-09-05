import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.api.teams import my_invitations, principal_name, respond_invitation
from app.auth.principal import Principal
from app.models import TeamInvitation


def principal(**overrides):
    return Principal(
        "recipient",
        {"name": "小明", **overrides},
    )


def db():
    session = MagicMock()
    session.scalar = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


def test_profile_name_normalized():
    assert principal_name(principal(name=" 小明 ")) == "小明"
    assert principal_name(principal(name=None)) is None


@pytest.mark.parametrize("action,status", [("accept", "accepted"), ("decline", "declined")])
def test_response_uses_locked_recipient_scope_and_atomic_commit(action, status):
    session = db()
    invite = TeamInvitation(
        id=uuid4(), team_id=uuid4(), email="person@example.com", role="member", status="pending"
    )
    session.scalar.side_effect = [invite, uuid4()]
    result = asyncio.run(respond_invitation(invite.id, action, principal(), session))
    assert result["status"] == invite.status == status
    statement = session.scalar.call_args_list[0].args[0].compile(dialect=postgresql.dialect())
    assert "FOR UPDATE" in str(statement)
    assert "recipient" in statement.params.values()
    assert "team_invitations.recipient_user_id IN" in str(statement)
    assert "users.external_id =" in str(statement)
    session.commit.assert_awaited_once()
    if action == "accept":
        membership = session.execute.call_args.args[0].compile(dialect=postgresql.dialect())
        assert "ON CONFLICT (team_id, user_id) DO NOTHING" in str(membership)
        assert membership.params["role"] == "member"
    else:
        session.execute.assert_not_awaited()


def test_wrong_account_or_missing_invitation_is_not_found():
    session = db()
    session.scalar.return_value = None
    with pytest.raises(HTTPException) as error:
        asyncio.run(respond_invitation(uuid4(), "accept", principal(), session))
    assert error.value.status_code == 404
    session.commit.assert_not_awaited()


@pytest.mark.parametrize("status", ["cancelled", "declined"])
def test_closed_invitation_cannot_be_accepted(status):
    session = db()
    session.scalar.return_value = TeamInvitation(status=status)
    with pytest.raises(HTTPException) as error:
        asyncio.run(respond_invitation(uuid4(), "accept", principal(), session))
    assert error.value.status_code == 409
    session.execute.assert_not_awaited()


def test_repeated_accept_is_idempotent():
    session = db()
    session.scalar.return_value = TeamInvitation(status="accepted", team_id=uuid4())
    assert (
        asyncio.run(respond_invitation(uuid4(), "accept", principal(), session))["status"]
        == "accepted"
    )
    session.execute.assert_not_awaited()


def test_inbox_filters_recipient_and_syncs_verified_name():
    session = db()
    session.execute.return_value = MagicMock()
    session.execute.return_value.all.return_value = []
    assert asyncio.run(my_invitations(principal(), session)) == []
    statements = [
        call.args[0].compile(dialect=postgresql.dialect())
        for call in session.execute.call_args_list
    ]
    assert statements[0].params["display_name"] == "小明"
    assert "recipient" in statements[1].params.values()
    assert "team_invitations.recipient_user_id IN" in str(statements[1])
    assert "pending" in statements[1].params.values()
