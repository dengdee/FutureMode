import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.models import MeetingState
from app.realtime.events import EventJournal
from app.realtime.rooms import RoomRegistry
from app.schemas.events import MeetingEvent
from app.websocket.events import (
    MeetingWebSocketContext,
    _publish_presence_event,
    _send_queued_events,
    get_meeting_websocket_context,
)


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

    async def context_override() -> MeetingWebSocketContext:
        return MeetingWebSocketContext(user_id=user_id, state=snapshot)

    app.dependency_overrides[get_meeting_websocket_context] = context_override
    try:
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/meetings/{meeting_id}/events") as socket:
                event = socket.receive_json()
    finally:
        app.dependency_overrides.pop(get_meeting_websocket_context, None)

    assert event["meeting_id"] == str(meeting_id)
    assert event["schema_version"] == 1
    assert event["payload"] == {
        "type": "meeting_state:snapshot",
        "state_version": 4,
        "state": {"topic": "roadmap"},
    }


def test_event_websocket_replays_events_strictly_after_the_requested_cursor() -> None:
    meeting_id = uuid4()
    user_id = uuid4()
    journal = EventJournal()
    replay_event = MeetingEvent(
        event_id=uuid4(),
        meeting_id=meeting_id,
        timestamp=datetime.now(UTC),
        schema_version=1,
        payload={"type": "transcript:new", "sequence": 1},
    )
    asyncio.run(journal.append(replay_event))

    async def context_override() -> MeetingWebSocketContext:
        return MeetingWebSocketContext(user_id=user_id, state=None)

    original_journal = app.state.event_journal
    app.state.event_journal = journal
    app.dependency_overrides[get_meeting_websocket_context] = context_override
    try:
        with TestClient(app) as client:
            with client.websocket_connect(
                f"/api/v1/meetings/{meeting_id}/events?after_cursor=0"
            ) as socket:
                snapshot = socket.receive_json()
                replayed = socket.receive_json()
    finally:
        app.state.event_journal = original_journal
        app.dependency_overrides.pop(get_meeting_websocket_context, None)

    assert snapshot["payload"]["type"] == "meeting_state:snapshot"
    assert replayed == replay_event.model_dump(mode="json")


def test_event_websocket_forwards_room_events_to_the_connected_client() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        rooms = RoomRegistry()
        connection = await rooms.connect(meeting_id, uuid4())
        delivered_event = MeetingEvent(
            event_id=uuid4(),
            meeting_id=meeting_id,
            timestamp=datetime.now(UTC),
            schema_version=1,
            payload={"type": "participant:update", "status": "joined"},
        )

        class Socket:
            def __init__(self) -> None:
                self.events = []
                self.sent = asyncio.Event()

            async def send_json(self, event) -> None:
                self.events.append(event)
                self.sent.set()

        socket = Socket()
        sender = asyncio.create_task(_send_queued_events(socket, connection))
        try:
            await rooms.publish(delivered_event)
            await asyncio.wait_for(socket.sent.wait(), timeout=1)
        finally:
            sender.cancel()
            with pytest.raises(asyncio.CancelledError):
                await sender

        assert socket.events == [delivered_event.model_dump(mode="json")]

    asyncio.run(scenario())


def test_presence_events_are_journaled_and_broadcast_to_the_meeting_room() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        user_id = uuid4()
        journal = EventJournal()
        rooms = RoomRegistry()
        recipient = await rooms.connect(meeting_id, uuid4())
        websocket = SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(event_journal=journal, room_registry=rooms))
        )

        await _publish_presence_event(websocket, meeting_id, user_id, status="joined")

        delivered = await recipient.next_event()
        stored = await journal.replay(meeting_id, after_cursor=0)
        assert delivered == stored[0].event
        assert delivered.payload == {
            "type": "participant:update",
            "user_id": str(user_id),
            "status": "joined",
        }

    asyncio.run(scenario())
