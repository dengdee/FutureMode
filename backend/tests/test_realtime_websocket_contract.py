from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


def test_event_websocket_rejects_a_connection_without_credentials() -> None:
    meeting_id = uuid4()

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as disconnected:
            with client.websocket_connect(f"/api/v1/meetings/{meeting_id}/events"):
                pass

    assert disconnected.value.code == 1008
