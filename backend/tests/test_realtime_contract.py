import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.meetings import database_session
from app.auth.principal import Principal, get_current_principal
from app.main import app
from app.models import MeetingState
from app.schemas.events import MeetingEvent


def test_meeting_state_requires_authentication() -> None:
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/api/v1/meetings/00000000-0000-0000-0000-000000000000/state"
            )

    response = asyncio.run(request())

    assert response.status_code == 401


def test_meeting_event_has_the_required_transport_metadata() -> None:
    event_id = uuid4()
    meeting_id = uuid4()
    timestamp = datetime.now(UTC)

    event = MeetingEvent(
        event_id=event_id,
        meeting_id=meeting_id,
        timestamp=timestamp,
        schema_version=1,
        payload={"type": "meeting_state:update", "state_version": 3},
    )

    assert event.model_dump(mode="json") == {
        "event_id": str(event_id),
        "meeting_id": str(meeting_id),
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "schema_version": 1,
        "payload": {"type": "meeting_state:update", "state_version": 3},
    }


def test_meeting_event_rejects_unsupported_schema_versions() -> None:
    with pytest.raises(ValidationError):
        MeetingEvent(
            event_id=uuid4(),
            meeting_id=uuid4(),
            timestamp=datetime.now(UTC),
            schema_version=0,
            payload={"type": "participant:update"},
        )


@pytest.mark.parametrize("forbidden_key", ["chain_of_thought", "private_prompt"])
def test_meeting_event_rejects_sensitive_payload_fields(forbidden_key: str) -> None:
    with pytest.raises(ValidationError):
        MeetingEvent(
            event_id=uuid4(),
            meeting_id=uuid4(),
            timestamp=datetime.now(UTC),
            schema_version=1,
            payload={"type": "agent:status", forbidden_key: "must not be transported"},
        )


def test_authorized_participant_receives_an_empty_state_snapshot() -> None:
    meeting_id = uuid4()
    response = asyncio.run(_get_state_snapshot(meeting_id, snapshot=None))

    assert response.status_code == 200
    assert response.json() == {
        "meeting_id": str(meeting_id),
        "state_version": 0,
        "state": {},
        "updated_at": None,
    }


def test_authorized_participant_receives_the_latest_state_snapshot() -> None:
    meeting_id = uuid4()
    updated_at = datetime.now(UTC)
    snapshot = MeetingState(
        meeting_id=meeting_id,
        state_version=4,
        state={"topic": "roadmap"},
        updated_at=updated_at,
    )

    response = asyncio.run(_get_state_snapshot(meeting_id, snapshot=snapshot))

    assert response.status_code == 200
    assert response.json() == {
        "meeting_id": str(meeting_id),
        "state_version": 4,
        "state": {"topic": "roadmap"},
        "updated_at": updated_at.isoformat().replace("+00:00", "Z"),
    }


async def _get_state_snapshot(meeting_id, snapshot: MeetingState | None):
    class Result:
        def first(self):
            return (object(), "member")

    class Session:
        async def execute(self, _):
            return Result()

        async def scalar(self, _):
            return snapshot

    async def principal_override() -> Principal:
        return Principal(subject="test-user", claims={})

    async def session_override():
        yield Session()

    app.dependency_overrides[get_current_principal] = principal_override
    app.dependency_overrides[database_session] = session_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(f"/api/v1/meetings/{meeting_id}/state")
    finally:
        app.dependency_overrides.pop(get_current_principal, None)
        app.dependency_overrides.pop(database_session, None)
