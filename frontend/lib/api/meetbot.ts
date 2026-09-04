import { http, request } from "./client";
import type { JoinMeetingRequest, MeetingBotResponse } from "../../types/api";

export function joinMeetingBot(payload: JoinMeetingRequest) {
  return request<MeetingBotResponse>(() => http.post("/meetbot/join", payload));
}
