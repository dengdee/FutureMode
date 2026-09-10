import { http, request } from "./client";
import type { VoiceBotStatus } from "../../types/api";

export type VoiceBotStatusResponse = {
  meeting_id: string;
  status: VoiceBotStatus | string;
  request_id: string | null;
  suggestion_id?: string | null;
  approved_text_version: number | null;
  message: string | null;
  generated_text?: string | null;
};

export function getVoiceBotStatus(meetingId: string) {
  return request<VoiceBotStatusResponse>(() => http.get(`/api/v1/meetings/${meetingId}/voice-bot/status`));
}

export function requestVoiceBot(meetingId: string, payload?: { suggestion_id?: string; approved_text?: string }) {
  return request<VoiceBotStatusResponse>(() => http.post(`/api/v1/meetings/${meetingId}/voice-bot/request`, payload ?? {}));
}

export function hostVoiceBotAction(meetingId: string, action: "approve" | "reject" | "retry" | "pause" | "resume") {
  return request<VoiceBotStatusResponse>(() => http.post(`/api/v1/meetings/${meetingId}/voice-bot/host-action`, { action }));
}

export function generateAndSpeakVoiceBot(
  meetingId: string,
  payload?: { prompt?: string; context?: string },
) {
  return request<VoiceBotStatusResponse>(() =>
    http.post(`/api/v1/meetings/${meetingId}/voice-bot/generate-and-speak`, payload ?? {}),
  );
}

export type VoiceObservationResponse = {
  meeting_id: string;
  suggestion_id: string;
  title: string;
  content: string;
  confidence: number | null;
  citations: Array<{ document_id: string; chunk_id: string }>;
};

export function observeMeetingVoiceBot(
  meetingId: string,
  payload?: { prompt?: string; transcript?: string },
) {
  return request<VoiceObservationResponse>(() =>
    http.post(`/api/v1/meetings/${meetingId}/voice-bot/observe`, payload ?? {}),
  );
}
