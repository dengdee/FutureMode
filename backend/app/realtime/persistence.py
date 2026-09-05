"""Neon/PostgreSQL-backed event journal for durable reconnect replay."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert

from app.config import Settings
from app.db.session import get_session
from app.models import MeetingEventLog
from app.realtime.events import StoredMeetingEvent
from app.schemas.events import MeetingEvent


class PostgresEventJournal:
    """Persist event IDs, cursors and recipient scope in PostgreSQL."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def append(
        self, event: MeetingEvent, *, recipient_user_id: UUID | None = None
    ) -> StoredMeetingEvent:
        stored, _ = await self.append_once(event, recipient_user_id=recipient_user_id)
        return stored

    async def append_once(
        self, event: MeetingEvent, *, recipient_user_id: UUID | None = None
    ) -> tuple[StoredMeetingEvent, bool]:
        async for session in get_session(self._settings):
            serialized_event = event.model_dump(mode="json")
            statement = (
                insert(MeetingEventLog)
                .values(
                    event_id=event.event_id,
                    meeting_id=event.meeting_id,
                    recipient_user_id=recipient_user_id,
                    timestamp=event.timestamp,
                    schema_version=event.schema_version,
                    payload=serialized_event["payload"],
                )
                .on_conflict_do_nothing(index_elements=["event_id"])
                .returning(MeetingEventLog)
            )
            record = (await session.scalars(statement)).first()
            created = record is not None
            if record is None:
                record = await session.scalar(
                    select(MeetingEventLog).where(MeetingEventLog.event_id == event.event_id)
                )
            await session.commit()
            if record is None:
                raise RuntimeError("event de-duplication record is unavailable")
            return _stored_event(record), created
        raise RuntimeError("database session is unavailable")

    async def replay(
        self, meeting_id: UUID, *, after_cursor: int, recipient_user_id: UUID | None = None
    ) -> list[StoredMeetingEvent]:
        if after_cursor < 0:
            raise ValueError("after_cursor must be non-negative")
        async for session in get_session(self._settings):
            audience = (
                MeetingEventLog.recipient_user_id.is_(None)
                if recipient_user_id is None
                else or_(
                    MeetingEventLog.recipient_user_id.is_(None),
                    MeetingEventLog.recipient_user_id == recipient_user_id,
                )
            )
            records = await session.scalars(
                select(MeetingEventLog)
                .where(
                    MeetingEventLog.meeting_id == meeting_id,
                    MeetingEventLog.sequence > after_cursor,
                    audience,
                )
                .order_by(MeetingEventLog.sequence)
            )
            return [_stored_event(record) for record in records]
        raise RuntimeError("database session is unavailable")

    async def latest_cursor(self, meeting_id: UUID) -> int:
        async for session in get_session(self._settings):
            cursor = await session.scalar(
                select(func.max(MeetingEventLog.sequence)).where(
                    MeetingEventLog.meeting_id == meeting_id
                )
            )
            return int(cursor or 0)
        raise RuntimeError("database session is unavailable")

    async def get(self, event_id: UUID) -> StoredMeetingEvent | None:
        async for session in get_session(self._settings):
            record = await session.scalar(
                select(MeetingEventLog).where(MeetingEventLog.event_id == event_id)
            )
            return _stored_event(record) if record is not None else None
        raise RuntimeError("database session is unavailable")


def _stored_event(record: MeetingEventLog) -> StoredMeetingEvent:
    return StoredMeetingEvent(
        sequence=record.sequence,
        event=MeetingEvent(
            event_id=record.event_id,
            meeting_id=record.meeting_id,
            timestamp=record.timestamp,
            schema_version=record.schema_version,
            payload=record.payload,
        ),
        recipient_user_id=record.recipient_user_id,
    )
