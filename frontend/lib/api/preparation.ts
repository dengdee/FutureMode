import { http, request } from "./client";
import type {
  PreparationDocument,
  PreparationMessage,
  PreparationPublishResult,
} from "../../types/api";

export const listPreparationMessages = (meetingId: string) =>
  request<PreparationMessage[]>(() =>
    http.get(`/api/v1/meetings/${meetingId}/preparation/messages`),
  );

export const createPreparationMessage = (meetingId: string, content: string) =>
  request<PreparationMessage[]>(() =>
    http.post(`/api/v1/meetings/${meetingId}/preparation/messages`, { content }),
  );

export const generatePreparationDocument = (meetingId: string) =>
  request<PreparationDocument>(() =>
    http.post(`/api/v1/meetings/${meetingId}/preparation/generate-document`),
  );
export const getPreparationDocument = (meetingId: string) =>
  request<PreparationDocument>(() =>
    http.get(`/api/v1/meetings/${meetingId}/preparation/document`),
  );
export const compilePreparationConsensus = (meetingId: string) =>
  request<{ meeting_id: string; content: string; source_count: number; generated_at: string }>(() =>
    http.post(`/api/v1/meetings/${meetingId}/preparation/compile-consensus`),
  );

export const publishPreparationToRag = (meetingId: string, documentId: string) =>
  request<PreparationPublishResult>(() =>
    http.post(`/api/v1/meetings/${meetingId}/preparation/publish-to-rag`, {
      document_id: documentId,
    }),
  );
