from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    team_id: UUID
    title: str = Field(min_length=1, max_length=255)
    scheduled_at: datetime | None = None
    ai_intervention_level: str = Field(default="medium", min_length=1, max_length=32)


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    scheduled_at: datetime | None = None
    ai_intervention_level: str | None = Field(default=None, min_length=1, max_length=32)


class ParticipantAdd(BaseModel):
    user_id: UUID
    role: str = Field(default="participant", min_length=1, max_length=32)


class ParticipantUpdate(BaseModel):
    role: str | None = Field(default=None, min_length=1, max_length=32)
    attendance_status: str | None = Field(default=None, min_length=1, max_length=32)


class AgendaItemCreate(BaseModel):
    position: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class AgendaItemUpdate(BaseModel):
    position: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)


class MeetingSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    team_id: UUID
    title: str
    scheduled_at: datetime | None
    status: str
    ai_intervention_level: str
