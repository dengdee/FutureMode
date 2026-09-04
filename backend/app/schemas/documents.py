from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    source_type: str
    status: str


class DocumentCreateResponse(BaseModel):
    id: UUID
    team_id: UUID
    status: str


class DocumentIngestRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5_000_000)
    chunk_size: int = Field(default=4_000, ge=500, le=20_000)


class DocumentIngestResponse(BaseModel):
    id: UUID
    version: int
    status: str
    chunk_count: int
    indexed_at: datetime | None
    retry_count: int = 0


class DocumentChunkCreateResponse(BaseModel):
    id: UUID
    document_id: UUID
    position: int


class DocumentDetail(DocumentSummary):
    metadata: dict[str, object]
    chunk_count: int
    version: int
    indexed_at: datetime | None
    index_error: str | None
    retry_count: int
    created_at: datetime | None


class DocumentVersionSummary(BaseModel):
    version: int
    content_hash: str
    storage_key: str | None
    chunk_count: int
    status: str
    created_at: datetime | None


class DocumentDownloadUrl(BaseModel):
    document_id: UUID
    url: str
    expires_in: int


class DocumentStorageStatus(BaseModel):
    document_id: UUID
    storage_key: str
    exists: bool


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
