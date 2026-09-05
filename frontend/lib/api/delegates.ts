import { http, request } from "./client";
import type { DelegateProfile } from "../../types/api";

export const listDelegates = (meetingId: string) => request<DelegateProfile[]>(() => http.get(`/api/v1/meetings/${meetingId}/delegates`));
export const createDelegate = (meetingId: string, payload: { stance: string; constraints?: string; must_raise?: string }) => request<Pick<DelegateProfile, "id" | "meeting_id" | "status">>(() => http.post(`/api/v1/meetings/${meetingId}/delegates`, payload));
