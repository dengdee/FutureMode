from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TranscriptBackupSegment(BaseModel):
    speaker_label: str = Field(min_length=1, max_length=255)
    speaker_user_id: UUID | None = None
    started_at: datetime
    ended_at: datetime | None = None
    text: str = Field(min_length=1, max_length=20_000)
    confidence: float | None = Field(default=None, ge=0, le=1)


class TranscriptBackupRequest(BaseModel):
    segments: list[TranscriptBackupSegment] = Field(min_length=1, max_length=500)
