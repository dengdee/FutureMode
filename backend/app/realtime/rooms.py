"""In-process meeting rooms and delivery queues."""

import asyncio
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.schemas.events import MeetingEvent


@dataclass
class RoomConnection:
    """A single connected client and its outbound event queue."""

    connection_id: UUID
    meeting_id: UUID
    user_id: UUID
    _events: asyncio.Queue[MeetingEvent] = field(default_factory=asyncio.Queue)

    async def next_event(self) -> MeetingEvent:
        return await self._events.get()

    def has_pending_events(self) -> bool:
        return not self._events.empty()


class RoomRegistry:
    """Route public room events and private user events within one process.

    Multi-instance deployment requires a shared pub/sub transport; this registry
    intentionally only owns local websocket connections.
    """

    def __init__(self) -> None:
        self._connections: dict[UUID, RoomConnection] = {}
        self._room_connections: dict[UUID, set[UUID]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, meeting_id: UUID, user_id: UUID) -> RoomConnection:
        connection = RoomConnection(
            connection_id=uuid4(),
            meeting_id=meeting_id,
            user_id=user_id,
        )
        async with self._lock:
            self._connections[connection.connection_id] = connection
            self._room_connections.setdefault(meeting_id, set()).add(connection.connection_id)
        return connection

    async def disconnect(self, connection: RoomConnection) -> None:
        async with self._lock:
            removed = self._connections.pop(connection.connection_id, None)
            if removed is None:
                return
            connection_ids = self._room_connections.get(removed.meeting_id)
            if connection_ids is None:
                return
            connection_ids.discard(removed.connection_id)
            if not connection_ids:
                del self._room_connections[removed.meeting_id]

    async def participants(self, meeting_id: UUID) -> set[UUID]:
        async with self._lock:
            return {
                self._connections[connection_id].user_id
                for connection_id in self._room_connections.get(meeting_id, set())
                if connection_id in self._connections
            }

    async def publish(
        self, event: MeetingEvent, *, recipient_user_id: UUID | None = None
    ) -> None:
        """Deliver a public event to a room, or a private event to one user."""
        async with self._lock:
            recipients = (
                self._connections[connection_id]
                for connection_id in self._room_connections.get(event.meeting_id, set())
                if connection_id in self._connections
            )
            for connection in recipients:
                if recipient_user_id is None or connection.user_id == recipient_user_id:
                    connection._events.put_nowait(event.model_copy(deep=True))
