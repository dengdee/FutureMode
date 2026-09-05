import { http, request } from "./client";
import type { AuthConfig, UserResponse } from "../../types/api";

export function getAuthConfig() { return request<AuthConfig>(() => http.get("/api/v1/auth/config")); }

export function getCurrentUser() {
  return request<UserResponse>(() => http.get("/api/v1/me"));
}

export function updateCurrentUser(payload: { display_name?: string; email?: string }) {
  return request<UserResponse>(() => http.patch("/api/v1/me", payload));
}
