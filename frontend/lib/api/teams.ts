import { http, request } from "./client";
import type { Invitation, Team, TeamMemberResponse, TeamResponse } from "../../types/api";

export function listTeams() { return request<TeamResponse>(() => http.get("/api/v1/teams")); }
export function listTeamMembers(teamId: string) { return request<TeamMemberResponse>(() => http.get(`/api/v1/teams/${teamId}/members`)); }
export function createTeam(payload: { name: string }) { return request<Team>(() => http.post("/api/v1/teams", payload)); }
export function updateTeamMember(teamId: string, userId: string, payload: { role: string }) { return request<TeamMemberResponse>(() => http.patch(`/api/v1/teams/${teamId}/members/${userId}`, payload)); }
export function removeTeamMember(teamId: string, userId: string) { return request<void>(() => http.delete(`/api/v1/teams/${teamId}/members/${userId}`)); }
export function updateTeam(teamId: string, payload: { name: string }) { return request<Team>(() => http.patch(`/api/v1/teams/${teamId}`, payload)); }
export function deleteTeam(teamId: string) { return request<void>(() => http.delete(`/api/v1/teams/${teamId}`)); }
export function createInvitation(teamId: string, payload: { email: string; role?: "admin" | "member" }) { return request<Invitation>(() => http.post(`/api/v1/teams/${teamId}/invitations`, payload)); }
export function listInvitations(teamId: string) { return request<Invitation[]>(() => http.get(`/api/v1/teams/${teamId}/invitations`)); }
export function cancelInvitation(teamId: string, invitationId: string) { return request<void>(() => http.delete(`/api/v1/teams/${teamId}/invitations/${invitationId}`)); }
