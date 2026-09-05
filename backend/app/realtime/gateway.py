"""Shared publish semantics for public and private realtime events."""

from uuid import UUID

from app.realtime.events import EventJournal, StoredMeetingEvent
from app.realtime.rooms import RoomRegistry
from app.schemas.events import MeetingEvent


async def publish_realtime_event(
    journal: EventJournal,
    rooms: RoomRegistry,
    event: MeetingEvent,
    *,
    recipient_user_id: UUID | None = None,
) -> StoredMeetingEvent:
    """Journal an event once and deliver it only to its authorized audience."""
    stored, was_added = await journal.append_once(event, recipient_user_id=recipient_user_id)
    if was_added:
        await rooms.publish(event, recipient_user_id=recipient_user_id)
    return stored
