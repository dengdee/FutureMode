import { http, request } from "./client";
import type {
  DocumentDetail,
  DocumentDownloadUrl,
  DocumentSearchResult,
  DocumentStorageStatus,
  DocumentSummary,
  DocumentVersion,
} from "../../types/api";
export const listDocumentChunks = (documentId: string) =>
  request<
    Array<{
      id: string;
      position: number;
      content: string;
      metadata: Record<string, unknown>;
    }>
  >(() => http.get(`/api/v1/documents/${documentId}/chunks`));
export const createDocumentChunk = (
  documentId: string,
  payload: {
    position: number;
    content: string;
    metadata?: Record<string, unknown>;
  },
) =>
  request<{ id: string; document_id: string; position: number }>(() =>
    http.post(`/api/v1/documents/${documentId}/chunks`, payload),
  );

export const listDocuments = (
  teamId: string,
  params?: { scope?: "team" | "meeting"; meeting_id?: string },
) =>
  request<DocumentSummary[]>(() =>
    http.get(`/api/v1/teams/${teamId}/documents`, { params }),
  );
export const createDocument = (
  teamId: string,
  payload: {
    name: string;
    source_type?: string;
    metadata?: Record<string, unknown>;
  },
) =>
  request<DocumentSummary>(() =>
    http.post(`/api/v1/teams/${teamId}/documents`, payload),
  );
export const uploadDocument = (documentId: string, file: File) => {
  const body = new FormData();
  body.append("file", file);
  return request<Record<string, unknown>>(() =>
    http.post(`/api/v1/documents/${documentId}/upload`, body, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  );
};
export const uploadDocuments = (
  teamId: string,
  files: File[],
  payload: { source_type: "team" | "meeting"; meeting_id?: string },
) => {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  body.append("source_type", payload.source_type);
  if (payload.meeting_id) body.append("meeting_id", payload.meeting_id);
  return request<Record<string, unknown>[]>(() =>
    http.post(`/api/v1/teams/${teamId}/documents/upload`, body, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  );
};
export const ingestDocument = (documentId: string, content: string) =>
  request<Record<string, unknown>>(() =>
    http.post(`/api/v1/documents/${documentId}/ingest`, { content }),
  );
export const deleteDocument = (documentId: string) =>
  request<void>(() => http.delete(`/api/v1/documents/${documentId}`));
export const getDocument = (documentId: string) =>
  request<DocumentDetail>(() => http.get(`/api/v1/documents/${documentId}`));
export const archiveDocument = (documentId: string) =>
  request<DocumentDetail>(() =>
    http.post(`/api/v1/documents/${documentId}/archive`),
  );
export const getDocumentDownloadUrl = (documentId: string, download = false) =>
  request<DocumentDownloadUrl>(() =>
    http.get(`/api/v1/documents/${documentId}/download-url`, {
      params: download ? { download: true } : undefined,
    }),
  );
export const getDocumentStorageStatus = (documentId: string) =>
  request<DocumentStorageStatus>(() =>
    http.get(`/api/v1/documents/${documentId}/storage-status`),
  );
export const listDocumentVersions = (documentId: string) =>
  request<DocumentVersion[]>(() =>
    http.get(`/api/v1/documents/${documentId}/versions`),
  );
export const restoreDocumentVersion = (documentId: string, version: number) =>
  request<Record<string, unknown>>(() =>
    http.post(`/api/v1/documents/${documentId}/versions/${version}/restore`),
  );
export const embedDocument = (documentId: string) =>
  request<Record<string, unknown>>(() =>
    http.post(`/api/v1/documents/${documentId}/embed`),
  );
export const searchMemory = (
  teamId: string,
  q: string,
  limit = 20,
  params?: { source_type?: string; version?: number },
) =>
  request<DocumentSearchResult[]>(() =>
    http.get(`/api/v1/teams/${teamId}/memory/hybrid-search`, {
      params: { q, limit, ...params },
    }),
  );
