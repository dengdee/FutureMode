from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    source_type: str
    status: str


class DocumentDetail(DocumentSummary):
    metadata: dict[str, object]
    chunk_count: int
    created_at: datetime | None


class DocumentChunkSummary(BaseModel):
    id: UUID
    position: int
    content: str
    metadata: dict[str, object]


class DocumentSearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str
    position: int
    content: str
    score: float
