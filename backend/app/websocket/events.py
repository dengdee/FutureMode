"""Authenticated WebSocket entry point for meeting realtime events."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_websocket_principal
from app.models import MeetingState
from app.schemas.events import MeetingEvent, MeetingStateSnapshot

router = APIRouter(tags=["realtime"])


@router.websocket("/api/v1/meetings/{meeting_id}/events")
async def meeting_events(
    websocket: WebSocket,
    meeting_id: UUID,
    principal: Principal = Depends(get_websocket_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    """Accept only authenticated users authorized for the requested meeting."""
    try:
        await authorized_meeting(meeting_id, principal, session)
        user_id = await find_user_id(session, principal.subject)
        state = await session.scalar(select(MeetingState).where(MeetingState.meeting_id == meeting_id))
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    connection = await websocket.app.state.room_registry.connect(meeting_id, user_id)
    snapshot = (
        MeetingStateSnapshot.model_validate(state)
        if state is not None
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
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        await websocket.app.state.room_registry.disconnect(connection)
