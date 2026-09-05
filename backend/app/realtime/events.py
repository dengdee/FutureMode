"""In-process event journal used for reconnect replay and de-duplication."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from app.schemas.events import MeetingEvent, MeetingEventEnvelope


@dataclass(frozen=True)
class StoredMeetingEvent:
    """An event together with its monotonic cursor inside one meeting."""

    sequence: int
    event: MeetingEvent
    recipient_user_id: UUID | None = None

    def to_envelope(self) -> MeetingEventEnvelope:
        return MeetingEventEnvelope(cursor=self.sequence, **self.event.model_dump())


class EventJournal:
    """Keep a bounded-lifetime, per-process event history.

    Production multi-instance replay will require a shared durable or pub/sub
    backend. This component defines the de-duplication and cursor semantics.
    """

    def __init__(self) -> None:
        self._events: dict[UUID, list[StoredMeetingEvent]] = defaultdict(list)
        self._events_by_id: dict[UUID, StoredMeetingEvent] = {}
        self._lock = asyncio.Lock()

    async def append(
        self, event: MeetingEvent, *, recipient_user_id: UUID | None = None
    ) -> StoredMeetingEvent:
        """Append an event once, returning its original entry on a duplicate ID."""
        stored, _ = await self.append_once(event, recipient_user_id=recipient_user_id)
        return stored

    async def append_once(
        self, event: MeetingEvent, *, recipient_user_id: UUID | None = None
    ) -> tuple[StoredMeetingEvent, bool]:
        """Append an event once and report whether this invocation created it."""
        async with self._lock:
            existing = self._events_by_id.get(event.event_id)
            if existing is not None:
                return existing, False
            stored = StoredMeetingEvent(
                sequence=len(self._events[event.meeting_id]) + 1,
                event=event.model_copy(deep=True),
                recipient_user_id=recipient_user_id,
            )
            self._events[event.meeting_id].append(stored)
            self._events_by_id[event.event_id] = stored
            return stored, True

    async def replay(
        self, meeting_id: UUID, *, after_cursor: int, recipient_user_id: UUID | None = None
    ) -> list[StoredMeetingEvent]:
        """Return events strictly newer than the client cursor for one meeting."""
        if after_cursor < 0:
            raise ValueError("after_cursor must be non-negative")
        async with self._lock:
            return [
                entry
                for entry in self._events[meeting_id]
                if entry.sequence > after_cursor
                and (entry.recipient_user_id is None or entry.recipient_user_id == recipient_user_id)
            ]

    async def latest_cursor(self, meeting_id: UUID) -> int:
        async with self._lock:
            return len(self._events[meeting_id])

    async def get(self, event_id: UUID) -> StoredMeetingEvent | None:
        """Look up a queued event's cursor before it is delivered to a client."""
        async with self._lock:
            return self._events_by_id.get(event_id)
