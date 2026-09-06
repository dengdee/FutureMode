from datetime import date, datetime
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


class BriefItem(BaseModel):
    position: int
    title: str
    description: str | None = None


class MeetingBrief(BaseModel):
    meeting_id: UUID
    generated_at: datetime
    generated_by: str
    summary: str
    agenda: list[BriefItem]


class TranscriptCreate(BaseModel):
    speaker_user_id: UUID | None = None
    speaker_label: str = Field(min_length=1, max_length=255)
    sequence: int = Field(ge=1)
    started_at: datetime
    ended_at: datetime | None = None
    text: str = Field(min_length=1, max_length=20_000)
    source: str = Field(default="fixture", min_length=1, max_length=32)
    confidence: float | None = Field(default=None, ge=0, le=1)


class TranscriptSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    meeting_id: UUID
    speaker_user_id: UUID | None
    speaker_label: str
    sequence: int
    started_at: datetime
    ended_at: datetime | None
    text: str
    source: str
    confidence: float | None


class ActionItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    assignee_user_id: UUID | None = None
    due_date: date | None = None
    status: str = Field(default="open", pattern="^(open|in_progress|done|cancelled)$")


class ActionItemUpdate(ActionItemCreate):
    title: str | None = Field(default=None, min_length=1, max_length=255)


class SuggestionStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|expanded|deferred|ignored|accepted)$")


class SuggestionSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    meeting_id: UUID
    state_version: int
    title: str
    content: str
    status: str
    confidence: float | None
    created_at: datetime


class SuggestionVoteCreate(BaseModel):
    vote: str = Field(pattern="^(support|reject|abstain)$")


class VoiceRequestCreate(BaseModel):
    suggestion_id: UUID | None = None
    approved_text: str | None = Field(default=None, max_length=20_000)


class VoiceSpeakRequest(BaseModel):
    """Optional context used when the approved voice request needs a fresh script."""

    prompt: str | None = Field(default=None, max_length=20_000)
    context: str | None = Field(default=None, max_length=20_000)


class VoiceBotStatusResponse(BaseModel):
    meeting_id: UUID
    status: str
    request_id: UUID | None = None
    suggestion_id: UUID | None = None
    approved_text_version: int | None = None
    message: str | None = None
    generated_text: str | None = None


class VoiceHostAction(BaseModel):
    action: str = Field(pattern="^(approve|reject|retry|pause|resume)$")


class PersonalMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class PersonalMessageSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    meeting_id: UUID
    role: str
    content: str
    created_at: datetime


class ContributionPublish(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    source_message_id: UUID | None = None


class PreparationMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class PreparationMessageSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    meeting_id: UUID
    role: str
    content: str
    created_at: datetime


class PreparationDocumentGenerateResponse(BaseModel):
    meeting_id: UUID
    document_id: UUID
    name: str
    content: str
    status: str
    generated_at: datetime


class PreparationPublishRequest(BaseModel):
    document_id: UUID


class PreparationPublishResponse(BaseModel):
    meeting_id: UUID
    document_id: UUID
    status: str
    chunk_count: int
    published_at: datetime


class DelegateProfileCreate(BaseModel):
    stance: str = Field(min_length=1, max_length=20_000)
    constraints: str | None = Field(default=None, max_length=20_000)
    must_raise: str | None = Field(default=None, max_length=20_000)


class ConsensusCreate(BaseModel):
    content: str = Field(min_length=1, max_length=50_000)


class ConsensusFeedbackCreate(BaseModel):
    decision: str = Field(pattern="^(agree|revise|reject)$")
    comment: str | None = Field(default=None, max_length=20_000)


class DocumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(default="text", min_length=1, max_length=32)
    metadata: dict[str, object] = Field(default_factory=dict)


class DocumentChunkCreate(BaseModel):
    position: int = Field(ge=1)
    content: str = Field(min_length=1, max_length=100_000)
    metadata: dict[str, object] = Field(default_factory=dict)
