import { http, request } from "./client";
import type { HealthResponse, ReadyResponse } from "../../types/api";

export function getHealth() {
  return request<HealthResponse>(() => http.get("/health"));
}

export function getReady() {
  return request<ReadyResponse>(() => http.get("/ready"));
}
