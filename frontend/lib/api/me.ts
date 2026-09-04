import { http, request } from "./client";
import type { UserResponse } from "../../types/api";

export function getCurrentUser() {
  return request<UserResponse>(() => http.get("/api/v1/me"));
}
