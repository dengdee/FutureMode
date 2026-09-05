import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.realtime.events import EventJournal
from app.schemas.events import MeetingEvent


def test_event_journal_assigns_monotonic_cursors_per_meeting() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        journal = EventJournal()

        first = await journal.append(_event(meeting_id))
        second = await journal.append(_event(meeting_id))

        assert first.sequence == 1
        assert second.sequence == 2

    asyncio.run(scenario())


def test_event_journal_deduplicates_a_repeated_event_id() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        event = _event(meeting_id)
        journal = EventJournal()

        first = await journal.append(event)
        duplicate = await journal.append(event)

        assert duplicate == first
        assert len(await journal.replay(meeting_id, after_cursor=0)) == 1

    asyncio.run(scenario())


def test_event_journal_replays_only_events_after_the_client_cursor() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        journal = EventJournal()
        first = await journal.append(_event(meeting_id))
        second = await journal.append(_event(meeting_id))

        replay = await journal.replay(meeting_id, after_cursor=first.sequence)

        assert [item.sequence for item in replay] == [second.sequence]

    asyncio.run(scenario())


def test_event_journal_does_not_replay_events_from_another_meeting() -> None:
    async def scenario() -> None:
        first_meeting_id = uuid4()
        second_meeting_id = uuid4()
        journal = EventJournal()
        await journal.append(_event(first_meeting_id))
        expected = await journal.append(_event(second_meeting_id))

        assert await journal.replay(second_meeting_id, after_cursor=0) == [expected]

    asyncio.run(scenario())


def test_event_journal_never_replays_a_private_event_to_another_user() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        recipient_user_id = uuid4()
        another_user_id = uuid4()
        journal = EventJournal()
        private_event = _event(meeting_id)
        public_event = _event(meeting_id)
        private_stored = await journal.append(private_event, recipient_user_id=recipient_user_id)
        public_stored = await journal.append(public_event)

        assert await journal.replay(meeting_id, after_cursor=0, recipient_user_id=recipient_user_id) == [
            private_stored,
            public_stored,
        ]
        assert await journal.replay(meeting_id, after_cursor=0, recipient_user_id=another_user_id) == [
            public_stored
        ]

    asyncio.run(scenario())


def _event(meeting_id):
    return MeetingEvent(
        event_id=uuid4(),
        meeting_id=meeting_id,
        timestamp=datetime.now(UTC),
        schema_version=1,
        payload={"type": "meeting_state:update"},
    )
