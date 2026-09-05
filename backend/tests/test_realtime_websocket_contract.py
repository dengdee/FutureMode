from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.meetings import database_session
from app.auth.principal import Principal, get_websocket_principal
from app.main import app
from app.models import MeetingState


def test_event_websocket_rejects_a_connection_without_credentials() -> None:
    meeting_id = uuid4()

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as disconnected:
            with client.websocket_connect(f"/api/v1/meetings/{meeting_id}/events"):
                pass

    assert disconnected.value.code == 1008


def test_event_websocket_sends_the_current_state_snapshot_after_connecting() -> None:
    meeting_id = uuid4()
    user_id = uuid4()
    snapshot = MeetingState(
        meeting_id=meeting_id,
        state_version=4,
        state={"topic": "roadmap"},
    )

    class Result:
        def first(self):
            return (object(), "member")

    class Session:
        def __init__(self) -> None:
            self.scalar_calls = 0

        async def execute(self, _):
            return Result()

        async def scalar(self, _):
            self.scalar_calls += 1
            return user_id if self.scalar_calls == 1 else snapshot

    async def principal_override() -> Principal:
        return Principal(subject="test-user", claims={})

    async def session_override():
        yield Session()

    app.dependency_overrides[get_websocket_principal] = principal_override
    app.dependency_overrides[database_session] = session_override
    try:
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/meetings/{meeting_id}/events") as socket:
                event = socket.receive_json()
    finally:
        app.dependency_overrides.pop(get_websocket_principal, None)
        app.dependency_overrides.pop(database_session, None)

    assert event["meeting_id"] == str(meeting_id)
    assert event["schema_version"] == 1
    assert event["payload"] == {
        "type": "meeting_state:snapshot",
        "state_version": 4,
        "state": {"topic": "roadmap"},
    }
