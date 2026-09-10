import { http, request } from "./client";
import type { LiveSnapshotResponse, VoteChoice } from "../../types/api";
import { listSuggestions } from "./meeting-features";
import { getMeeting } from "./meetings";
import { getMeetingState } from "./realtime";
import { getVoiceBotStatus } from "./voice";

export function getLiveSnapshot(meetingId: string) {
  return Promise.all([
    getMeeting(meetingId),
    listSuggestions(meetingId),
    getMeetingState(meetingId),
    getVoiceBotStatus(meetingId),
  ]).then(([meeting, suggestions, state, voiceBot]) => ({
    meeting,
    suggestions,
    state: { ...state.state, voice_bot: voiceBot.status },
    state_version: state.state_version,
    updated_at: state.updated_at,
  } satisfies LiveSnapshotResponse));
}

export function voteOnSuggestion(meetingId: string, suggestionId: string, choice: VoteChoice) {
  const vote = choice === "support" ? "support" : choice === "later" ? "abstain" : "reject";
  return request<Record<string, unknown>>(() => http.post(`/api/v1/meetings/${meetingId}/suggestions/${suggestionId}/vote`, { vote }));
}

export function updateInterventionPolicy(meetingId: string, policy: Record<string, unknown>) {
  return request<Record<string, unknown>>(() => http.patch(`/api/v1/meetings/${meetingId}`, policy));
}
