from uuid import UUID

from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    meeting_id: UUID
    text: str
    model: str
