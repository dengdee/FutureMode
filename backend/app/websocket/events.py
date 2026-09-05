"""Authenticated WebSocket entry point for meeting realtime events."""

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.api.meetings import authorized_meeting, find_user_id
from app.auth.principal import Principal, get_websocket_principal
from app.config import get_settings
from app.db.session import get_session
from app.models import MeetingState
from app.realtime.rooms import RoomConnection
from app.schemas.events import MeetingEvent, MeetingStateSnapshot

router = APIRouter(tags=["realtime"])


@dataclass(frozen=True)
class MeetingWebSocketContext:
    user_id: UUID
    state: MeetingState | None


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
            return MeetingWebSocketContext(user_id=user_id, state=state)
    except HTTPException:
        return None
    return None


@router.websocket("/api/v1/meetings/{meeting_id}/events")
async def meeting_events(
    websocket: WebSocket,
    meeting_id: UUID,
    context: MeetingWebSocketContext | None = Depends(get_meeting_websocket_context),
    after_cursor: int = Query(default=0, ge=0),
) -> None:
    """Accept only authenticated users authorized for the requested meeting."""
    if context is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    connection = await websocket.app.state.room_registry.connect(meeting_id, context.user_id)
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
        MeetingEvent(
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
    for stored_event in await websocket.app.state.event_journal.replay(
        meeting_id, after_cursor=after_cursor
    ):
        await websocket.send_json(stored_event.event.model_dump(mode="json"))
    sender = asyncio.create_task(_send_queued_events(websocket, connection))
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()
        with suppress(asyncio.CancelledError):
            await sender
        await websocket.app.state.room_registry.disconnect(connection)


async def _send_queued_events(websocket: WebSocket, connection: RoomConnection) -> None:
    """Forward local room events to one accepted WebSocket connection."""
    while True:
        event = await connection.next_event()
        await websocket.send_json(event.model_dump(mode="json"))
