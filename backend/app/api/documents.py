from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from uuid import UUID, uuid4

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.meetings import authorized_meeting, database_session
from app.auth.principal import Principal, get_current_principal
from app.config import get_settings
from app.models import Document, DocumentChunk, DocumentVersion, Meeting, TeamMember, User
from app.schemas.documents import (
    DocumentChunkCreateResponse,
    DocumentChunkSummary,
    DocumentCreateResponse,
    DocumentDetail,
    DocumentDownloadUrl,
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentSearchResult,
    DocumentStorageStatus,
    DocumentSummary,
    DocumentVersionSummary,
)
from app.schemas.meeting import DocumentChunkCreate, DocumentCreate
from app.services.embeddings import EmbeddingConfigurationError, embed_texts
from app.services.storage import (
    StorageConfigurationError,
    create_download_url,
    delete_file,
    file_exists,
    get_file,
    put_file,
)

router = APIRouter(prefix="/api/v1", tags=["documents"])
settings = get_settings()


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


@router.post(
    "/teams/{team_id}/documents",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    team_id: UUID,
    payload: DocumentCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentCreateResponse:
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


@router.get("/teams/{team_id}/documents", response_model=list[DocumentSummary])
async def list_documents(
    team_id: UUID,
    scope: str | None = Query(default=None, pattern="^(team|meeting)$"),
    meeting_id: UUID | None = Query(default=None),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentSummary]:
    await team_access(team_id, principal, session)
    filters = [Document.team_id == team_id]
    if scope == "team":
        filters.append(Document.source_type == "team")
    elif scope == "meeting":
        if meeting_id is None:
            return []
        filters.append(Document.source_type == "meeting")
        filters.append(Document.metadata_json["meeting_id"].astext == str(meeting_id))
    docs = (await session.scalars(select(Document).where(*filters))).all()
    return [
        {
            "id": str(d.id),
            "team_id": str(d.team_id),
            "name": d.name,
            "source_type": d.source_type,
            "status": d.status,
        }
        for d in docs
    ]


@router.post(
    "/teams/{team_id}/documents/upload",
    response_model=list[DocumentIngestResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    team_id: UUID,
    files: list[UploadFile] = File(...),
    source_type: str = Form(default="team", pattern="^(team|meeting)$"),
    meeting_id: UUID | None = Form(default=None),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentIngestResponse]:
    """Create and ingest a confirmed group of files in one multipart request."""
    if not files:
        raise HTTPException(status_code=400, detail="at least one file is required")
    if source_type == "meeting" and meeting_id is None:
        raise HTTPException(status_code=422, detail="meeting_id is required for meeting documents")
    user = await team_access(team_id, principal, session)
    if meeting_id is not None:
        meeting = await session.scalar(
            select(Meeting).where(Meeting.id == meeting_id, Meeting.team_id == team_id)
        )
        if meeting is None:
            raise HTTPException(status_code=404, detail="meeting not found in this team")
    results: list[DocumentIngestResponse] = []
    for file in files:
        document = Document(
            team_id=team_id,
            uploaded_by=user.id,
            name=file.filename or "upload",
            source_type=source_type,
            metadata_json={"meeting_id": str(meeting_id)} if meeting_id else {},
        )
        session.add(document)
        await session.commit()
        try:
            results.append(await upload_text_document(document.id, file, principal, session))
        except HTTPException:
            await session.delete(document)
            await session.commit()
            raise
    return results


@router.post(
    "/documents/{document_id}/chunks",
    response_model=DocumentChunkCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chunk(
    document_id: UUID,
    payload: DocumentChunkCreate,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentChunkCreateResponse:
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


@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkSummary])
async def list_chunks(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentChunkSummary]:
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
    return [
        {
            "id": str(c.id),
            "position": c.position,
            "content": c.content,
            "metadata": c.metadata_json,
        }
        for c in rows
    ]


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentDetail:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    chunk_count = await session.scalar(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
    )
    return {
        "id": str(document.id),
        "team_id": str(document.team_id),
        "name": document.name,
        "source_type": document.source_type,
        "status": document.status,
        "metadata": document.metadata_json,
        "chunk_count": int(chunk_count or 0),
        "version": document.version,
        "indexed_at": document.indexed_at,
        "index_error": document.index_error,
        "retry_count": document.retry_count,
        "created_at": document.created_at,
    }


@router.post("/documents/{document_id}/archive", response_model=DocumentDetail)
async def archive_document(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentDetail:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    document.status = "archived"
    await session.commit()
    chunk_count = await session.scalar(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
    )
    return DocumentDetail(
        id=document.id,
        team_id=document.team_id,
        name=document.name,
        source_type=document.source_type,
        status=document.status,
        metadata=document.metadata_json,
        chunk_count=int(chunk_count or 0),
        version=document.version,
        indexed_at=document.indexed_at,
        index_error=document.index_error,
        retry_count=document.retry_count,
        created_at=document.created_at,
    )


@router.get("/documents/{document_id}/download-url", response_model=DocumentDownloadUrl)
async def document_download_url(
    document_id: UUID,
    download: bool = Query(default=False),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentDownloadUrl:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    storage_key = document.metadata_json.get("storage_key")
    if not isinstance(storage_key, str) or not storage_key:
        raise HTTPException(status_code=404, detail="document file not found")
    try:
        url = await create_download_url(storage_key, settings, download=download)
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=502, detail="file storage is unavailable") from None
    return DocumentDownloadUrl(
        document_id=document.id,
        url=url,
        expires_in=settings.r2_presigned_expiry_seconds,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> None:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    version_keys = (
        await session.scalars(
            select(DocumentVersion.storage_key).where(DocumentVersion.document_id == document_id)
        )
    ).all()
    storage_keys = {
        key
        for key in [document.metadata_json.get("storage_key"), *version_keys]
        if isinstance(key, str) and key
    }
    for storage_key in storage_keys:
        try:
            await delete_file(storage_key, settings)
        except StorageConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except (BotoCoreError, ClientError):
            raise HTTPException(status_code=502, detail="file storage is unavailable") from None
    await session.delete(document)
    await session.commit()


@router.get("/documents/{document_id}/storage-status", response_model=DocumentStorageStatus)
async def document_storage_status(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentStorageStatus:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    storage_key = document.metadata_json.get("storage_key")
    if not isinstance(storage_key, str) or not storage_key:
        raise HTTPException(status_code=404, detail="document file not found")
    try:
        exists = await file_exists(storage_key, settings)
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=502, detail="file storage is unavailable") from None
    return DocumentStorageStatus(document_id=document.id, storage_key=storage_key, exists=exists)


@router.post(
    "/documents/{document_id}/ingest",
    response_model=DocumentIngestResponse,
)
async def ingest_document(
    document_id: UUID,
    payload: DocumentIngestRequest,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentIngestResponse:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    document.status = "indexing"
    document.index_error = None
    document.version += 1
    await session.flush()
    await session.execute(
        DocumentChunk.__table__.delete().where(DocumentChunk.document_id == document_id)
    )

    chunks = [
        DocumentChunk(
            document_id=document_id,
            position=index,
            content=payload.content[start : start + payload.chunk_size],
        )
        for index, start in enumerate(range(0, len(payload.content), payload.chunk_size), start=1)
    ]
    session.add_all(chunks)
    document.status = "ready"
    document.indexed_at = datetime.now(UTC)
    session.add(
        DocumentVersion(
            document_id=document.id,
            version=document.version,
            content_hash=sha256(payload.content.encode("utf-8")).hexdigest(),
            chunk_count=len(chunks),
            status=document.status,
        )
    )
    await session.commit()
    return DocumentIngestResponse(
        id=document.id,
        version=document.version,
        status=document.status,
        chunk_count=len(chunks),
        indexed_at=document.indexed_at,
        retry_count=document.retry_count,
    )


@router.post("/documents/{document_id}/upload", response_model=DocumentIngestResponse)
async def upload_text_document(
    document_id: UUID,
    file: UploadFile = File(...),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentIngestResponse:
    filename = (file.filename or "").lower()
    is_pdf = file.content_type == "application/pdf" or filename.endswith(".pdf")
    is_text = file.content_type in {"text/plain", "text/markdown"} or filename.endswith(".txt")
    if not is_pdf and not is_text:
        raise HTTPException(status_code=415, detail="only text and PDF files are supported")
    raw_content = await file.read(5_000_001)
    if len(raw_content) > 5_000_000:
        raise HTTPException(status_code=413, detail="file is too large")
    if is_pdf:
        try:
            reader = PdfReader(BytesIO(raw_content))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            raise HTTPException(status_code=400, detail="could not extract PDF text") from None
    else:
        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="file must be UTF-8 encoded") from None
    if not content.strip():
        raise HTTPException(status_code=400, detail="file contains no extractable text")
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    storage_key = (
        f"teams/{document.team_id}/documents/{document.id}/{uuid4()}-"
        f"{(file.filename or 'upload').replace('/', '_').replace(chr(92), '_')}"
    )
    try:
        await put_file(
            storage_key,
            raw_content,
            file.content_type or "application/octet-stream",
            settings,
        )
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=502, detail="file storage is unavailable") from None
    document.metadata_json = {
        **document.metadata_json,
        "storage_key": storage_key,
        "original_filename": file.filename or "upload",
        "content_type": file.content_type,
    }
    result = await ingest_document(
        document_id,
        DocumentIngestRequest(content=content),
        principal,
        session,
    )
    latest_version = await session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version == result.version,
        )
    )
    if latest_version is not None:
        latest_version.storage_key = storage_key
        await session.commit()
    return result


@router.get("/documents/{document_id}/versions", response_model=list[DocumentVersionSummary])
async def list_document_versions(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentVersionSummary]:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    versions = (
        await session.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version.desc())
        )
    ).all()
    return list(versions)


@router.post(
    "/documents/{document_id}/versions/{version}/restore",
    response_model=DocumentIngestResponse,
)
async def restore_document_version(
    document_id: UUID,
    version: int,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> DocumentIngestResponse:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    source = await session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.document_id == document_id, DocumentVersion.version == version
        )
    )
    if source is None or not source.storage_key:
        raise HTTPException(status_code=404, detail="version source file not found")
    try:
        raw_content = await get_file(source.storage_key, settings)
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=502, detail="file storage is unavailable") from None
    try:
        if document.metadata_json.get("content_type") == "application/pdf":
            reader = PdfReader(BytesIO(raw_content))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            content = raw_content.decode("utf-8")
    except (UnicodeDecodeError, Exception):
        raise HTTPException(status_code=400, detail="could not restore document version") from None
    return await ingest_document(
        document_id, DocumentIngestRequest(content=content), principal, session
    )


@router.post("/documents/{document_id}/embed")
async def embed_document(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> dict[str, object]:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    await team_access(document.team_id, principal, session)
    chunks = (
        await session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.position)
        )
    ).all()
    if not chunks:
        raise HTTPException(status_code=409, detail="document has no chunks")
    if len(chunks) > settings.embedding_max_chunks:
        raise HTTPException(status_code=413, detail="document has too many chunks to embed")
    try:
        vectors: list[list[float]] = []
        for start in range(0, len(chunks), settings.embedding_batch_size):
            vectors.extend(
                await embed_texts(
                    [
                        chunk.content
                        for chunk in chunks[start : start + settings.embedding_batch_size]
                    ],
                    settings,
                )
            )
    except EmbeddingConfigurationError as exc:
        document.status = "failed"
        document.index_error = str(exc)
        document.retry_count += 1
        await session.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError:
        document.status = "failed"
        document.index_error = "embedding provider unavailable"
        document.retry_count += 1
        await session.commit()
        raise HTTPException(status_code=502, detail="embedding provider unavailable") from None
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk.embedding = vector
    document.status = "embedded"
    document.index_error = None
    await session.commit()
    return {
        "document_id": str(document_id),
        "status": document.status,
        "embedded_chunks": len(chunks),
    }


@router.get("/teams/{team_id}/memory/search", response_model=list[DocumentSearchResult])
async def search_memory(
    team_id: UUID,
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    source_type: str | None = Query(default=None, max_length=32),
    version: int | None = Query(default=None, ge=1),
    metadata_key: str | None = Query(default=None, max_length=64),
    metadata_value: str | None = Query(default=None, max_length=255),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentSearchResult]:
    """Search team document chunks with PostgreSQL full-text search."""
    await team_access(team_id, principal, session)
    document_vector = func.to_tsvector("simple", DocumentChunk.content)
    query_vector = func.plainto_tsquery("simple", q)
    rank = func.ts_rank_cd(document_vector, query_vector).label("rank")
    filters = [
        Document.team_id == team_id,
        Document.status.in_({"ready", "embedded"}),
        document_vector.op("@@")(query_vector),
    ]
    if source_type:
        filters.append(Document.source_type == source_type)
    if version is not None:
        filters.append(Document.version == version)
    if metadata_key and metadata_value is not None:
        filters.append(Document.metadata_json.contains({metadata_key: metadata_value}))
    rows = (
        await session.execute(
            select(DocumentChunk, Document, rank)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(*filters)
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


@router.get("/teams/{team_id}/memory/hybrid-search", response_model=list[DocumentSearchResult])
async def hybrid_search_memory(
    team_id: UUID,
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    source_type: str | None = Query(default=None, max_length=32),
    version: int | None = Query(default=None, ge=1),
    metadata_key: str | None = Query(default=None, max_length=64),
    metadata_value: str | None = Query(default=None, max_length=255),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentSearchResult]:
    """Search team memory using embedding similarity and lexical matching."""
    await team_access(team_id, principal, session)
    try:
        query_vector = (await embed_texts([q], settings))[0]
    except EmbeddingConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="embedding provider unavailable") from None
    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    text_rank = func.ts_rank_cd(
        func.to_tsvector("simple", DocumentChunk.content),
        func.plainto_tsquery("simple", q),
    )
    hybrid_score = ((1 - distance) * 0.7 + text_rank * 0.3).label("hybrid_score")
    filters = [
        Document.team_id == team_id,
        Document.status == "embedded",
        DocumentChunk.embedding.is_not(None),
    ]
    if source_type:
        filters.append(Document.source_type == source_type)
    if version is not None:
        filters.append(Document.version == version)
    if metadata_key and metadata_value is not None:
        filters.append(Document.metadata_json.contains({metadata_key: metadata_value}))
    rows = (
        await session.execute(
            select(DocumentChunk, Document, hybrid_score)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(*filters)
            .order_by(hybrid_score.desc(), DocumentChunk.position)
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


@router.get(
    "/meetings/{meeting_id}/memory/search", response_model=list[DocumentSearchResult]
)
async def search_meeting_memory(
    meeting_id: UUID,
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentSearchResult]:
    """Search only preparation documents published for the current meeting."""
    await authorized_meeting(meeting_id, principal, session)
    document_vector = func.to_tsvector("simple", DocumentChunk.content)
    query_vector = func.plainto_tsquery("simple", q)
    rank = func.ts_rank_cd(document_vector, query_vector).label("rank")
    rows = (
        await session.execute(
            select(DocumentChunk, Document, rank)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.source_type == "preparation",
                Document.status.in_({"ready", "embedded"}),
                Document.metadata_json.contains({"meeting_id": str(meeting_id)}),
                document_vector.op("@@")(query_vector),
            )
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


@router.get(
    "/meetings/{meeting_id}/memory/hybrid-search", response_model=list[DocumentSearchResult]
)
async def hybrid_search_meeting_memory(
    meeting_id: UUID,
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(database_session),
) -> list[DocumentSearchResult]:
    """Use embedding plus lexical ranking over the meeting's preparation RAG only."""
    await authorized_meeting(meeting_id, principal, session)
    try:
        query_vector = (await embed_texts([q], settings))[0]
    except EmbeddingConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="embedding provider unavailable") from None
    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    text_rank = func.ts_rank_cd(
        func.to_tsvector("simple", DocumentChunk.content),
        func.plainto_tsquery("simple", q),
    )
    hybrid_score = ((1 - distance) * 0.7 + text_rank * 0.3).label("hybrid_score")
    rows = (
        await session.execute(
            select(DocumentChunk, Document, hybrid_score)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.source_type == "preparation",
                Document.status == "embedded",
                Document.metadata_json.contains({"meeting_id": str(meeting_id)}),
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(hybrid_score.desc(), DocumentChunk.position)
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
