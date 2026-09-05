import { http, request } from "./client";
import type { MeetingBrief, MeetingCreateRequest, MeetingSummary, MeetingUpdateRequest } from "../../types/api";

export function listMeetings() { return request<MeetingSummary[]>(() => http.get("/api/v1/meetings")); }
export function getMeeting(meetingId: string) { return request<MeetingSummary>(() => http.get(`/api/v1/meetings/${meetingId}`)); }
export function createMeeting(payload: MeetingCreateRequest) { return request<MeetingSummary>(() => http.post("/api/v1/meetings", payload)); }
export function updateMeeting(meetingId: string, payload: MeetingUpdateRequest) { return request<MeetingSummary>(() => http.patch(`/api/v1/meetings/${meetingId}`, payload)); }
export function startMeeting(meetingId: string) { return request<MeetingSummary>(() => http.post(`/api/v1/meetings/${meetingId}/start`)); }
export function endMeeting(meetingId: string) { return request<MeetingSummary>(() => http.post(`/api/v1/meetings/${meetingId}/end`)); }
export function cancelMeeting(meetingId: string) { return request<MeetingSummary>(() => http.post(`/api/v1/meetings/${meetingId}/cancel`)); }
export function createMeetingBrief(meetingId: string) { return request<MeetingBrief>(() => http.post(`/api/v1/meetings/${meetingId}/brief`)); }
