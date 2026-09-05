"""Authenticated WebSocket entry point for meeting realtime events."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.meetings import authorized_meeting, find_user_id
from app.auth.principal import Principal, get_websocket_principal
from app.config import get_settings
from app.db.session import get_session

router = APIRouter(tags=["realtime"])


@router.websocket("/api/v1/meetings/{meeting_id}/events")
async def meeting_events(
    websocket: WebSocket,
    meeting_id: UUID,
) -> None:
    """Accept only authenticated users authorized for the requested meeting."""
    try:
        principal: Principal = await get_websocket_principal(websocket, get_settings())
        async for session in get_session(websocket.app.state.settings):
            await authorized_meeting(meeting_id, principal, session)
            user_id = await find_user_id(session, principal.subject)
            break
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    connection = await websocket.app.state.room_registry.connect(meeting_id, user_id)
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        await websocket.app.state.room_registry.disconnect(connection)
