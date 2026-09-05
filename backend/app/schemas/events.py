"""Stable schemas for realtime meeting event transport."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_FORBIDDEN_PAYLOAD_KEYS = {"chain_of_thought", "private_prompt"}


def _contains_forbidden_payload_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in _FORBIDDEN_PAYLOAD_KEYS or _contains_forbidden_payload_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


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

    @field_validator("payload")
    @classmethod
    def payload_must_not_contain_sensitive_reasoning(cls, value: dict[str, object]) -> dict[str, object]:
        if _contains_forbidden_payload_key(value):
            raise ValueError("event payload contains a prohibited sensitive field")
        return value


class MeetingStateSnapshot(BaseModel):
    """The latest public state available when a client joins or reconnects."""

    model_config = {"from_attributes": True}

    meeting_id: UUID
    state_version: int = Field(ge=0)
    state: dict[str, object]
    updated_at: datetime | None


class MeetingStateUpdate(BaseModel):
    """A compare-and-set request for the public meeting state."""

    expected_state_version: int = Field(ge=0)
    state: dict[str, object]
