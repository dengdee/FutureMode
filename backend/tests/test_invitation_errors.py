import asyncio
import json

import pytest
from fastapi import HTTPException, Request

from app.main import http_exception_handler


@pytest.mark.parametrize("reason", ["missing", "unverified"])
def test_invitation_failure_preserves_specific_safe_reason(reason):
    request = Request({"type": "http", "state": {"request_id": "test"}})
    response = asyncio.run(http_exception_handler(
        request, HTTPException(403, f"invitation_identity_email_{reason}"),
    ))
    error = json.loads(response.body)["error"]
    assert response.status_code == 403
    assert error["code"] == f"invitation_email_{reason}"
    assert error["request_id"] == "test"
