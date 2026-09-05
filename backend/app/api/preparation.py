from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session, find_user_id
from app.auth.principal import Principal, get_current_principal
from app.config import Settings, get_settings
from app.models import Document, DocumentChunk, DocumentVersion, PreparationMessage
from app.schemas.meeting import (
    PreparationDocumentGenerateResponse,
    PreparationMessageCreate,
    PreparationMessageSummary,
    PreparationPublishRequest,
    PreparationPublishResponse,
)
from app.services.llm import (
    LLMConfigurationError,
    LLMProviderError,
    complete_preparation,
    generate_preparation_document,
)

router = APIRouter(prefix="/api/v1", tags=["preparation"])


@router.get(
    "/meetings/{meeting_id}/preparation/messages", response_model=list[PreparationMessageSummary]
)
async def list_preparation_messages(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
):
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    return list(
        (
            await session.scalars(
                select(PreparationMessage)
                .where(
                    PreparationMessage.meeting_id == meeting_id,
                    PreparationMessage.user_id == user_id,
                )
                .order_by(PreparationMessage.created_at)
            )
        ).all()
    )


@router.post(
    "/meetings/{meeting_id}/preparation/messages",
    response_model=list[PreparationMessageSummary],
    status_code=status.HTTP_201_CREATED,
)
async def create_preparation_message(
    meeting_id: UUID,
    payload: PreparationMessageCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
    settings: Settings = Depends(get_settings),
):
    await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    history = list(
        (
            await session.scalars(
                select(PreparationMessage)
                .where(
                    PreparationMessage.meeting_id == meeting_id,
                    PreparationMessage.user_id == user_id,
                )
                .order_by(PreparationMessage.created_at)
            )
        ).all()
    )
    user_message = PreparationMessage(
        meeting_id=meeting_id, user_id=user_id, role="user", content=payload.content
    )
    session.add(user_message)
    try:
        answer = await complete_preparation(
            [{"role": item.role, "content": item.content} for item in history]
            + [{"role": "user", "content": payload.content}],
            settings,
        )
    except LLMConfigurationError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError:
        await session.rollback()
        raise HTTPException(status_code=502, detail="LLM provider unavailable") from None
    assistant_message = PreparationMessage(
        meeting_id=meeting_id, user_id=user_id, role="assistant", content=answer
    )
    session.add(assistant_message)
    try:
        await session.commit()
        await session.refresh(user_message)
        await session.refresh(assistant_message)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return [user_message, assistant_message]


@router.post(
    "/meetings/{meeting_id}/preparation/generate-document",
    response_model=PreparationDocumentGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_preparation_document_endpoint(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
    settings: Settings = Depends(get_settings),
) -> PreparationDocumentGenerateResponse:
    """Generate a persisted draft brief from the caller's private preparation chat."""
    meeting = await authorized_meeting(meeting_id, principal, session)
    user_id = await find_user_id(session, principal.subject)
    messages = list(
        (
            await session.scalars(
                select(PreparationMessage)
                .where(
                    PreparationMessage.meeting_id == meeting_id,
                    PreparationMessage.user_id == user_id,
                )
                .order_by(PreparationMessage.created_at)
            )
        ).all()
    )
    if not messages:
        raise HTTPException(status_code=409, detail="preparation chat is empty")
    try:
        content = await generate_preparation_document(
            [{"role": item.role, "content": item.content} for item in messages], settings
        )
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError:
        raise HTTPException(status_code=502, detail="LLM provider unavailable") from None

    now = datetime.now(UTC)
    document = Document(
        team_id=meeting.team_id,
        uploaded_by=user_id,
        name=f"{meeting.title} - 議前討論",
        source_type="preparation",
        status="draft",
        metadata_json={
            "meeting_id": str(meeting_id),
            "generated_by": str(user_id),
            "generated_at": now.isoformat(),
            "published_to_rag": False,
        },
    )
    session.add(document)
    await session.flush()
    session.add(
        DocumentChunk(
            document_id=document.id,
            position=1,
            content=content,
            metadata_json={"source": "preparation", "meeting_id": str(meeting_id)},
        )
    )
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return PreparationDocumentGenerateResponse(
        meeting_id=meeting_id,
        document_id=document.id,
        name=document.name,
        content=content,
        status=document.status,
        generated_at=now,
    )


@router.post(
    "/meetings/{meeting_id}/preparation/publish-to-rag",
    response_model=PreparationPublishResponse,
)
async def publish_preparation_to_rag(
    meeting_id: UUID,
    payload: PreparationPublishRequest,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> PreparationPublishResponse:
    """Publish a generated preparation draft to the team's searchable document memory."""
    meeting = await authorized_meeting(meeting_id, principal, session)
    document = await session.scalar(
        select(Document).where(
            Document.id == payload.document_id,
            Document.team_id == meeting.team_id,
            Document.source_type == "preparation",
        )
    )
    if document is None or document.metadata_json.get("meeting_id") != str(meeting_id):
        raise HTTPException(status_code=404, detail="preparation document not found")
    chunks = list(
        (
            await session.scalars(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document.id)
                .order_by(DocumentChunk.position)
            )
        ).all()
    )
    if not chunks:
        raise HTTPException(status_code=409, detail="preparation document has no content")
    if document.status in {"ready", "embedded"}:
        return PreparationPublishResponse(
            meeting_id=meeting_id,
            document_id=document.id,
            status=document.status,
            chunk_count=len(chunks),
            published_at=document.indexed_at or datetime.now(UTC),
        )

    published_at = datetime.now(UTC)
    content = "\n\n".join(chunk.content for chunk in chunks)
    document.status = "ready"
    document.indexed_at = published_at
    document.index_error = None
    document.metadata_json = {**document.metadata_json, "published_to_rag": True}
    session.add(
        DocumentVersion(
            document_id=document.id,
            version=document.version,
            content_hash=sha256(content.encode("utf-8")).hexdigest(),
            chunk_count=len(chunks),
            status=document.status,
        )
    )
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="database is unavailable") from None
    return PreparationPublishResponse(
        meeting_id=meeting_id,
        document_id=document.id,
        status=document.status,
        chunk_count=len(chunks),
        published_at=published_at,
    )
