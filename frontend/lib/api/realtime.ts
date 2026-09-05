import { http, request } from "./client";
import type { MeetingStateSnapshot } from "../../types/api";

export function getMeetingState(meetingId: string) {
  return request<MeetingStateSnapshot>(() => http.get(`/api/v1/meetings/${meetingId}/state`));
}
