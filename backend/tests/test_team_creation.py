"""Authenticated creation must provision a local user and atomically grant admin membership."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.api.teams import database_session
from app.auth.principal import Principal, get_current_principal
from app.main import app
from app.models import Team, TeamMember, User


@pytest.fixture
def session():
    session = MagicMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock(return_value=uuid4())
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    async def flush():
        for call in session.add.call_args_list:
            if isinstance(call.args[0], Team):
                call.args[0].id = uuid4()

    session.flush = AsyncMock(side_effect=flush)
    return session


def send(session, authenticated=True):
    async def db():
        yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[database_session] = db
    if authenticated:
        app.dependency_overrides[get_current_principal] = lambda: Principal("verified-user", {})

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as client:
            return await client.post("/api/v1/teams", json={"name": "My team"})

    try:
        return asyncio.run(run())
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_first_creation_provisions_user_and_admin(session):
    response = send(session)
    assert response.status_code == 201
    statement = session.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    assert statement.params["external_id"] == "verified-user"
    assert "ON CONFLICT (external_id) DO NOTHING" in str(statement)
    added = [call.args[0] for call in session.add.call_args_list]
    team, membership = added
    assert isinstance(membership, TeamMember)
    assert membership.user_id == session.scalar.return_value
    assert membership.team_id == team.id
    assert membership.role == response.json()["role"] == "admin"
    assert not any(isinstance(item, User) for item in added)
    session.commit.assert_awaited_once()


def test_commit_failure_rolls_back_entire_creation(session):
    session.commit.side_effect = SQLAlchemyError("failure")
    assert send(session).status_code == 503
    session.rollback.assert_awaited_once()


def test_unverified_request_cannot_provision_user(session):
    assert send(session, authenticated=False).status_code == 401
    session.execute.assert_not_awaited()
    session.commit.assert_not_awaited()
