import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.teams import update_member_role
from app.auth.principal import Principal
from app.models import TeamMember, User
from app.models.core import MembershipRole
from app.schemas.team import RoleUpdate


def test_only_admin_and_member_can_be_assigned():
    assert set(MembershipRole) == {"admin", "member"}
    assert RoleUpdate(role="admin").role == "admin"
    assert RoleUpdate(role="member").role == "member"
    with pytest.raises(ValidationError):
        RoleUpdate(role="owner")


@pytest.mark.parametrize("role", ["admin", "member"])
def test_admin_can_adjust_other_members(role):
    team_id, actor_id, target_id = uuid4(), uuid4(), uuid4()
    target = TeamMember(team_id=team_id, user_id=target_id, role="member")
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[
        User(id=actor_id, external_id="actor"),
        TeamMember(team_id=team_id, user_id=actor_id, role="admin"), target,
    ])
    session.commit = AsyncMock()
    result = asyncio.run(update_member_role(
        team_id, target_id, RoleUpdate(role=role), Principal("actor", {}), session,
    ))
    assert result["role"] == role
    session.commit.assert_awaited_once()


def test_member_cannot_promote_themselves():
    actor_id, team_id = uuid4(), uuid4()
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[
        User(id=actor_id, external_id="actor"),
        TeamMember(team_id=team_id, user_id=actor_id, role="member"),
    ])
    session.commit = AsyncMock()
    with pytest.raises(HTTPException) as error:
        asyncio.run(update_member_role(
            team_id, actor_id, RoleUpdate(role="admin"), Principal("actor", {}), session,
        ))
    assert error.value.status_code == 403
    session.commit.assert_not_awaited()
