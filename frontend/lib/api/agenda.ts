import { http, request } from "./client";
import type { AgendaItemCreateRequest, AgendaItemCreateResponse, AgendaItemResponse, AgendaItemsResponse, AgendaItemUpdateRequest } from "../../types/api";

export function addAgendaItem(meetingId: string, payload: AgendaItemCreateRequest) { return request<AgendaItemCreateResponse>(() => http.post(`/api/v1/meetings/${meetingId}/agenda`, payload)); }
export function listAgendaItems(meetingId: string) { return request<AgendaItemsResponse>(() => http.get(`/api/v1/meetings/${meetingId}/agenda`)); }
export function updateAgendaItem(meetingId: string, itemId: string, payload: AgendaItemUpdateRequest) { return request<AgendaItemResponse>(() => http.patch(`/api/v1/meetings/${meetingId}/agenda/${itemId}`, payload)); }
export function removeAgendaItem(meetingId: string, itemId: string) { return request<void>(() => http.delete(`/api/v1/meetings/${meetingId}/agenda/${itemId}`)); }
