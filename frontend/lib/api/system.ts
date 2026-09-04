import { http, request } from "./client";
import type { HealthResponse } from "../../types/api";

export function getHealth() {
  return request<HealthResponse>(() => http.get("/health"));
}

export function getReady() {
  return request<Record<string, unknown>>(() => http.get("/ready"));
}
