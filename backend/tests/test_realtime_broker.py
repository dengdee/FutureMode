import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.realtime.events import EventJournal
from app.realtime.gateway import publish_realtime_event
from app.realtime.rooms import RoomRegistry
from app.schemas.events import MeetingEvent


def test_new_event_is_published_to_the_cross_instance_broker_once() -> None:
    async def scenario() -> None:
        class Broker:
            def __init__(self) -> None:
                self.published = []

            async def publish(self, event, *, recipient_user_id=None) -> None:
                self.published.append((event, recipient_user_id))

        meeting_id = uuid4()
        event = MeetingEvent(
            event_id=uuid4(),
            meeting_id=meeting_id,
            timestamp=datetime.now(UTC),
            schema_version=1,
            payload={"type": "meeting_state:update"},
        )
        broker = Broker()
        journal = EventJournal()
        rooms = RoomRegistry()

        await publish_realtime_event(journal, rooms, event, broker=broker)
        await publish_realtime_event(journal, rooms, event, broker=broker)

        assert broker.published == [(event, None)]

    asyncio.run(scenario())
