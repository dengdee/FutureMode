import { http, request } from "./client";
import type { LiveSnapshotResponse, VoteChoice } from "../../types/api";
import { listSuggestions } from "./meeting-features";
import { getMeeting } from "./meetings";

export function getLiveSnapshot(meetingId: string) {
  return Promise.all([getMeeting(meetingId), listSuggestions(meetingId)]).then(([meeting, suggestions]) => ({ meeting, suggestions } satisfies LiveSnapshotResponse));
}

export function voteOnSuggestion(meetingId: string, suggestionId: string, choice: VoteChoice) {
  const vote = choice === "support" ? "support" : choice === "later" ? "abstain" : "reject";
  return request<Record<string, unknown>>(() => http.post(`/api/v1/meetings/${meetingId}/suggestions/${suggestionId}/vote`, { vote }));
}

export function updateInterventionPolicy(meetingId: string, policy: Record<string, unknown>) {
  return request<Record<string, unknown>>(() => http.patch(`/api/v1/meetings/${meetingId}`, policy));
}
