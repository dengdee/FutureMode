"""Stable schemas for realtime meeting event transport."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MeetingEvent(BaseModel):
    """An event delivered through the meeting realtime channel.

    The payload is intentionally generic at the transport boundary. Event-specific
    schemas will be introduced alongside their producers and consumers.
    """

    event_id: UUID
    meeting_id: UUID
    timestamp: datetime
    schema_version: int = Field(ge=1)
    payload: dict[str, object]


class MeetingStateSnapshot(BaseModel):
    """The latest public state available when a client joins or reconnects."""

    model_config = {"from_attributes": True}

    meeting_id: UUID
    state_version: int = Field(ge=0)
    state: dict[str, object]
    updated_at: datetime | None
