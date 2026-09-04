import { http, request } from "./client";
import type { ParticipantAddRequest, ParticipantCreateResponse, ParticipantResponse, ParticipantsResponse, ParticipantUpdateRequest } from "../../types/api";

export function addParticipant(meetingId: string, payload: ParticipantAddRequest) { return request<ParticipantCreateResponse>(() => http.post(`/api/v1/meetings/${meetingId}/participants`, payload)); }
export function listParticipants(meetingId: string) { return request<ParticipantsResponse>(() => http.get(`/api/v1/meetings/${meetingId}/participants`)); }
export function updateParticipant(meetingId: string, userId: string, payload: ParticipantUpdateRequest) { return request<ParticipantResponse>(() => http.patch(`/api/v1/meetings/${meetingId}/participants/${userId}`, payload)); }
export function removeParticipant(meetingId: string, userId: string) { return request<void>(() => http.delete(`/api/v1/meetings/${meetingId}/participants/${userId}`)); }
