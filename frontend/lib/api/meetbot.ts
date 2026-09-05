import { http, request } from "./client";
import type { BotStatusResponse, JoinMeetingRequest, JoinMeetingResponse, MeetingBotResponse } from "../../types/api";

export function joinMeetingBot(payload: JoinMeetingRequest) {
  return request<JoinMeetingResponse>(() => http.post("/meetbot/join", payload, { headers: { "Idempotency-Key": crypto.randomUUID() } }));
}
export function getMeetingBotStatus(botId: string) { return request<BotStatusResponse>(() => http.get(`/meetbot/${botId}`)); }
export function leaveMeetingBot(botId: string) { return request<{ bot_id: string; status: string }>(() => http.post(`/meetbot/${botId}/leave`)); }
export function speakMeetingBot(payload?: { approved_text_id?: string; approved_text_version?: number }) { return request<Record<string, string>>(() => http.post("/meetbot/speak", payload)); }
