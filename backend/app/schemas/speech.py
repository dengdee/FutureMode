from uuid import UUID

from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    meeting_id: UUID
    transcript_id: UUID
    sequence: int
    text: str
    model: str
