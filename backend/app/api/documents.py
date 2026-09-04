from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import database_session
from app.auth.principal import Principal, get_current_principal
from app.models import Document, DocumentChunk, TeamMember, User
from app.schemas.meeting import DocumentChunkCreate, DocumentCreate

router = APIRouter(prefix="/api/v1", tags=["documents"])


async def team_access(team_id: UUID, principal: Principal, session: AsyncSession) -> User:
    user = await session.scalar(select(User).where(User.external_id == principal.subject))
    member = await session.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == (user.id if user else None)
        )
    )
    if user is None or member is None:
        raise HTTPException(status_code=404, detail="team not found")
    return user


@router.post("/teams/{team_id}/documents", status_code=status.HTTP_201_CREATED)
async def create_document(
    team_id: UUID,
    payload: DocumentCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, str]:
    user = await team_access(team_id, principal, session)
    document = Document(
        team_id=team_id,
        uploaded_by=user.id,
        name=payload.name,
        source_type=payload.source_type,
        metadata_json=payload.metadata,
    )
    session.add(document)
    await session.commit()
    return {"id": str(document.id), "team_id": str(team_id), "status": document.status}


@router.get("/teams/{team_id}/documents")
async def list_documents(
    team_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, object]]:
    await team_access(team_id, principal, session)
    docs = (await session.scalars(select(Document).where(Document.team_id == team_id))).all()
    return [
        {"id": str(d.id), "name": d.name, "source_type": d.source_type, "status": d.status}
        for d in docs
    ]


@router.post("/documents/{document_id}/chunks", status_code=status.HTTP_201_CREATED)
async def create_chunk(
    document_id: UUID,
    payload: DocumentChunkCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    chunk = DocumentChunk(
        document_id=document_id,
        position=payload.position,
        content=payload.content,
        metadata_json=payload.metadata,
    )
    session.add(chunk)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="document chunk position already exists"
        ) from None
    return {"id": str(chunk.id), "document_id": str(document_id), "position": chunk.position}


@router.get("/documents/{document_id}/chunks")
async def list_chunks(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, object]]:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    rows = (
        await session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.position)
        )
    ).all()
    return [{"id": str(c.id), "position": c.position, "content": c.content} for c in rows]


@router.get("/teams/{team_id}/memory/search")
async def search_memory(
    team_id: UUID,
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[dict[str, object]]:
    """Search team document chunks with PostgreSQL full-text search."""
    await team_access(team_id, principal, session)
    document_vector = func.to_tsvector("simple", DocumentChunk.content)
    query_vector = func.plainto_tsquery("simple", q)
    rank = func.ts_rank_cd(document_vector, query_vector).label("rank")
    rows = (
        await session.execute(
            select(DocumentChunk, Document, rank)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.team_id == team_id, document_vector.op("@@")(query_vector))
            .order_by(rank.desc(), DocumentChunk.position)
            .limit(limit)
        )
    ).all()
    return [
        {
            "chunk_id": str(chunk.id),
            "document_id": str(document.id),
            "document_name": document.name,
            "position": chunk.position,
            "content": chunk.content,
            "score": float(score),
        }
        for chunk, document, score in rows
    ]
