"""Authenticated WebSocket entry point for meeting realtime events."""

import asyncio
import json
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import select

from app.api.meetings import authorized_meeting, find_user_id
from app.auth.principal import Principal, get_websocket_principal
from app.config import get_settings
from app.db.session import get_session
from app.models import MeetingEventCursor, MeetingState
from app.realtime.events import EventJournal
from app.realtime.gateway import publish_realtime_event
from app.realtime.rooms import RoomConnection
from app.schemas.events import (
    MeetingEvent,
    MeetingEventAck,
    MeetingEventEnvelope,
    MeetingStateSnapshot,
)

router = APIRouter(tags=["realtime"])


@dataclass(frozen=True)
class MeetingWebSocketContext:
    user_id: UUID
    state: MeetingState | None
    last_event_cursor: int = 0


async def get_meeting_websocket_context(
    websocket: WebSocket, meeting_id: UUID
) -> MeetingWebSocketContext | None:
    """Authorize a WebSocket without letting HTTP exception handlers handle it."""
    try:
        principal: Principal = await get_websocket_principal(websocket, get_settings())
        async for session in get_session(websocket.app.state.settings):
            await authorized_meeting(meeting_id, principal, session)
            user_id = await find_user_id(session, principal.subject)
            state = await session.scalar(
                select(MeetingState).where(MeetingState.meeting_id == meeting_id)
            )
            cursor = await session.scalar(
                select(MeetingEventCursor.last_event_sequence).where(
                    MeetingEventCursor.meeting_id == meeting_id,
                    MeetingEventCursor.user_id == user_id,
                )
            )
            return MeetingWebSocketContext(
                user_id=user_id,
                state=state,
                last_event_cursor=int(cursor or 0),
            )
    except HTTPException:
        return None
    return None


@router.websocket("/api/v1/meetings/{meeting_id}/events")
async def meeting_events(
    websocket: WebSocket,
    meeting_id: UUID,
    context: MeetingWebSocketContext | None = Depends(get_meeting_websocket_context),
    after_cursor: int | None = Query(default=None, ge=0),
) -> None:
    """Accept only authenticated users authorized for the requested meeting."""
    if websocket.app.state.settings.realtime_require_broker and (
        websocket.app.state.realtime_broker is None
    ):
        await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
        return
    if context is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    was_present = context.user_id in await websocket.app.state.room_registry.participants(
        meeting_id
    )
    connection = await websocket.app.state.room_registry.connect(meeting_id, context.user_id)
    broker = websocket.app.state.realtime_broker
    if broker is None:
        joined_globally = not was_present
    else:
        try:
            joined_globally = await broker.join_presence(
                meeting_id, context.user_id, connection.connection_id
            )
        except (RedisError, OSError):
            joined_globally = not was_present
    snapshot = (
        MeetingStateSnapshot.model_validate(context.state)
        if context.state is not None
        else MeetingStateSnapshot(
            meeting_id=meeting_id,
            state_version=0,
            state={},
            updated_at=None,
        )
    )
    await websocket.send_json(
        MeetingEventEnvelope(
            cursor=0,
            event_id=uuid4(),
            meeting_id=meeting_id,
            timestamp=datetime.now(UTC),
            schema_version=1,
            payload={
                "type": "meeting_state:snapshot",
                "state_version": snapshot.state_version,
                "state": snapshot.state,
            },
        ).model_dump(mode="json")
    )
    requested_cursor = after_cursor if after_cursor is not None else context.last_event_cursor
    replay_cursor = min(requested_cursor, context.last_event_cursor)
    for stored_event in await websocket.app.state.event_journal.replay(
        meeting_id, after_cursor=replay_cursor, recipient_user_id=context.user_id
    ):
        await websocket.send_json(stored_event.to_envelope().model_dump(mode="json"))
    sender = asyncio.create_task(
        _send_queued_events(websocket, connection, websocket.app.state.event_journal)
    )
    if joined_globally:
        await _publish_presence_event(websocket, meeting_id, context.user_id, status="joined")
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            await _handle_client_message(websocket, meeting_id, context.user_id, message)
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()
        with suppress(asyncio.CancelledError):
            await sender
        await websocket.app.state.room_registry.disconnect(connection)
        if broker is None:
            participants = await websocket.app.state.room_registry.participants(meeting_id)
            left_globally = context.user_id not in participants
        else:
            try:
                left_globally = await broker.leave_presence(
                    meeting_id, context.user_id, connection.connection_id
                )
            except (RedisError, OSError):
                participants = await websocket.app.state.room_registry.participants(meeting_id)
                left_globally = context.user_id not in participants
        if left_globally:
            await _publish_presence_event(websocket, meeting_id, context.user_id, status="left")


async def _send_queued_events(
    websocket: WebSocket, connection: RoomConnection, journal: EventJournal
) -> None:
    """Forward local room events to one accepted WebSocket connection."""
    while True:
        event = await connection.next_event()
        stored_event = await journal.get(event.event_id)
        if stored_event is not None:
            await websocket.send_json(stored_event.to_envelope().model_dump(mode="json"))


async def _publish_presence_event(
    websocket: WebSocket, meeting_id: UUID, user_id: UUID, *, status: str
) -> None:
    """Record and broadcast an aggregate join or leave transition."""
    event = MeetingEvent(
        event_id=uuid4(),
        meeting_id=meeting_id,
        timestamp=datetime.now(UTC),
        schema_version=1,
        payload={
            "type": "participant:update",
            "user_id": str(user_id),
            "status": status,
        },
    )
    try:
        await publish_realtime_event(
            websocket.app.state.event_journal,
            websocket.app.state.room_registry,
            event,
            broker=getattr(websocket.app.state, "realtime_broker", None),
        )
    except (RedisError, OSError):
        # Redis is optional; the local journal and room delivery remain valid.
        await publish_realtime_event(
            websocket.app.state.event_journal,
            websocket.app.state.room_registry,
            event,
        )


async def _handle_client_message(
    websocket: WebSocket, meeting_id: UUID, user_id: UUID, message: dict[str, object]
) -> None:
    """Accept only validated acknowledgement messages from a connected client."""
    raw_message = message.get("text")
    try:
        if not isinstance(raw_message, str):
            raise ValueError("a JSON text message is required")
        acknowledgement = MeetingEventAck.model_validate(json.loads(raw_message))
        latest_cursor = await websocket.app.state.event_journal.latest_cursor(meeting_id)
        if acknowledgement.cursor > latest_cursor:
            raise ValueError("cursor is ahead of the server event journal")
        await _persist_event_cursor(websocket, meeting_id, user_id, acknowledgement.cursor)
    except (ValueError, ValidationError, json.JSONDecodeError):
        await _send_protocol_error(websocket, meeting_id, "invalid_realtime_message")


async def _persist_event_cursor(
    websocket: WebSocket, meeting_id: UUID, user_id: UUID, cursor: int
) -> None:
    """Advance the durable cursor monotonically after a client acknowledgement."""
    async for session in get_session(websocket.app.state.settings):
        record = await session.scalar(
            select(MeetingEventCursor)
            .where(
                MeetingEventCursor.meeting_id == meeting_id,
                MeetingEventCursor.user_id == user_id,
            )
            .with_for_update()
        )
        if record is None:
            session.add(
                MeetingEventCursor(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    last_event_sequence=cursor,
                )
            )
        elif cursor > record.last_event_sequence:
            record.last_event_sequence = cursor
        await session.commit()
        return


async def _send_protocol_error(websocket: WebSocket, meeting_id: UUID, code: str) -> None:
    """Send a safe, connection-local protocol error without journaling it."""
    await websocket.send_json(
        MeetingEventEnvelope(
            cursor=0,
            event_id=uuid4(),
            meeting_id=meeting_id,
            timestamp=datetime.now(UTC),
            schema_version=1,
            payload={"type": "error", "code": code},
        ).model_dump(mode="json")
    )
