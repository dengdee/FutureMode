import { http, request } from "./client";
import type { AddonAccessTokenResponse, LiveSnapshotResponse, VoteChoice } from "../../types/api";

export function getLiveSnapshot(meetingId: string) {
  return request<LiveSnapshotResponse>(() => http.get(`/api/v1/meetings/${meetingId}/live-snapshot`));
}

export function createMeetingAccessToken(meetingId: string) {
  return request<AddonAccessTokenResponse>(() => http.post(`/api/v1/meetings/${meetingId}/access-token`));
}

export function voteOnSuggestion(meetingId: string, suggestionId: string, choice: VoteChoice) {
  return request<Record<string, unknown>>(() => http.post(`/api/v1/meetings/${meetingId}/suggestions/${suggestionId}/vote`, { choice }));
}

export function updateInterventionPolicy(meetingId: string, policy: Record<string, unknown>) {
  return request<Record<string, unknown>>(() => http.patch(`/api/v1/meetings/${meetingId}/intervention-policy`, policy));
}
