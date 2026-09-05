import { http, request } from "./client";
import type { DocumentSearchResult, DocumentSummary } from "../../types/api";

export const listDocuments = (teamId: string) => request<DocumentSummary[]>(() => http.get(`/api/v1/teams/${teamId}/documents`));
export const createDocument = (teamId: string, payload: { name: string; source_type?: string; metadata?: Record<string, unknown> }) => request<DocumentSummary>(() => http.post(`/api/v1/teams/${teamId}/documents`, payload));
export const uploadDocument = (documentId: string, file: File) => { const body = new FormData(); body.append("file", file); return request<Record<string, unknown>>(() => http.post(`/api/v1/documents/${documentId}/upload`, body, { headers: { "Content-Type": "multipart/form-data" } })); };
export const ingestDocument = (documentId: string, content: string) => request<Record<string, unknown>>(() => http.post(`/api/v1/documents/${documentId}/ingest`, { content }));
export const deleteDocument = (documentId: string) => request<void>(() => http.delete(`/api/v1/documents/${documentId}`));
export const searchMemory = (teamId: string, q: string, limit = 20) => request<DocumentSearchResult[]>(() => http.get(`/api/v1/teams/${teamId}/memory/hybrid-search`, { params: { q, limit } }));
