import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.realtime.rooms import RoomRegistry
from app.schemas.events import MeetingEvent


def test_public_events_are_delivered_only_to_connections_in_the_same_room() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        another_meeting_id = uuid4()
        rooms = RoomRegistry()
        recipient = await rooms.connect(meeting_id, uuid4())
        other_room_recipient = await rooms.connect(another_meeting_id, uuid4())

        event = _event(meeting_id)
        await rooms.publish(event)

        assert await recipient.next_event() == event
        assert not other_room_recipient.has_pending_events()

    asyncio.run(scenario())


def test_private_events_are_delivered_only_to_the_named_recipient() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        recipient_user_id = uuid4()
        rooms = RoomRegistry()
        recipient = await rooms.connect(meeting_id, recipient_user_id)
        other_participant = await rooms.connect(meeting_id, uuid4())

        event = _event(meeting_id)
        await rooms.publish(event, recipient_user_id=recipient_user_id)

        assert await recipient.next_event() == event
        assert not other_participant.has_pending_events()

    asyncio.run(scenario())


def test_presence_is_scoped_to_a_meeting_and_removed_on_disconnect() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        another_meeting_id = uuid4()
        user_id = uuid4()
        rooms = RoomRegistry()
        connection = await rooms.connect(meeting_id, user_id)
        await rooms.connect(another_meeting_id, uuid4())

        assert await rooms.participants(meeting_id) == {user_id}
        await rooms.disconnect(connection)
        assert await rooms.participants(meeting_id) == set()

    asyncio.run(scenario())


def _event(meeting_id):
    return MeetingEvent(
        event_id=uuid4(),
        meeting_id=meeting_id,
        timestamp=datetime.now(UTC),
        schema_version=1,
        payload={"type": "participant:update"},
    )
