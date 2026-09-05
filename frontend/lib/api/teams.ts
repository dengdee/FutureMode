import { http, request } from "./client";
import type { Team, TeamMemberResponse, TeamResponse } from "../../types/api";

export function listTeams() { return request<TeamResponse>(() => http.get("/api/v1/teams")); }
export function listTeamMembers(teamId: string) { return request<TeamMemberResponse>(() => http.get(`/api/v1/teams/${teamId}/members`)); }
export function createTeam(payload: { name: string }) { return request<Team>(() => http.post("/api/v1/teams", payload)); }
export function updateTeamMember(teamId: string, userId: string, payload: { role: string }) { return request<TeamMemberResponse>(() => http.patch(`/api/v1/teams/${teamId}/members/${userId}`, payload)); }
export function removeTeamMember(teamId: string, userId: string) { return request<void>(() => http.delete(`/api/v1/teams/${teamId}/members/${userId}`)); }
