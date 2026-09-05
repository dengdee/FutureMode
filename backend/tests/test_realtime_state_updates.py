import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import app
from app.schemas.events import MeetingEventAck, MeetingStateUpdate


def test_state_update_accepts_the_initial_state_version() -> None:
    update = MeetingStateUpdate(expected_state_version=0, state={"topic": "kickoff"})

    assert update.expected_state_version == 0
    assert update.state == {"topic": "kickoff"}


def test_state_update_rejects_a_negative_expected_version() -> None:
    with pytest.raises(ValidationError):
        MeetingStateUpdate(expected_state_version=-1, state={})


def test_meeting_state_update_requires_authentication() -> None:
    meeting_id = uuid4()

    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.patch(
                f"/api/v1/meetings/{meeting_id}/state",
                json={"expected_state_version": 0, "state": {}},
            )

    response = asyncio.run(request())

    assert response.status_code == 401


def test_event_ack_rejects_a_negative_cursor() -> None:
    with pytest.raises(ValidationError):
        MeetingEventAck(type="ack", cursor=-1)
