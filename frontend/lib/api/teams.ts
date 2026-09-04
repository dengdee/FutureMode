import { http, request } from "./client";
import type { TeamMemberResponse, TeamResponse } from "../../types/api";

export function listTeams() { return request<TeamResponse>(() => http.get("/api/v1/teams")); }
export function listTeamMembers(teamId: string) { return request<TeamMemberResponse>(() => http.get(`/api/v1/teams/${teamId}/members`)); }
