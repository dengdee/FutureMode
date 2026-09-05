"""In-process event journal used for reconnect replay and de-duplication."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from app.schemas.events import MeetingEvent


@dataclass(frozen=True)
class StoredMeetingEvent:
    """An event together with its monotonic cursor inside one meeting."""

    sequence: int
    event: MeetingEvent


class EventJournal:
    """Keep a bounded-lifetime, per-process event history.

    Production multi-instance replay will require a shared durable or pub/sub
    backend. This component defines the de-duplication and cursor semantics.
    """

    def __init__(self) -> None:
        self._events: dict[UUID, list[StoredMeetingEvent]] = defaultdict(list)
        self._events_by_id: dict[UUID, StoredMeetingEvent] = {}
        self._lock = asyncio.Lock()

    async def append(self, event: MeetingEvent) -> StoredMeetingEvent:
        """Append an event once, returning its original entry on a duplicate ID."""
        async with self._lock:
            existing = self._events_by_id.get(event.event_id)
            if existing is not None:
                return existing
            stored = StoredMeetingEvent(
                sequence=len(self._events[event.meeting_id]) + 1,
                event=event.model_copy(deep=True),
            )
            self._events[event.meeting_id].append(stored)
            self._events_by_id[event.event_id] = stored
            return stored

    async def replay(self, meeting_id: UUID, *, after_cursor: int) -> list[StoredMeetingEvent]:
        """Return events strictly newer than the client cursor for one meeting."""
        if after_cursor < 0:
            raise ValueError("after_cursor must be non-negative")
        async with self._lock:
            return [
                entry
                for entry in self._events[meeting_id]
                if entry.sequence > after_cursor
            ]
