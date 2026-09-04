import axios, { type AxiosResponse } from "axios";
import type { ApiError, HealthResponse, JoinMeetingRequest, MeetingBotResponse } from "../../types/api";
import { authClient } from "../auth/client";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiClientError extends Error implements ApiError {
  status?: number;
  code?: string;
  requestId?: string;

  constructor(error: ApiError) {
    super(error.message);
    this.name = "ApiClientError";
    this.status = error.status;
    this.code = error.code;
    this.requestId = error.requestId;
  }
}

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: { Accept: "application/json" },
});

http.interceptors.request.use(async (config) => {
  // Neon Auth keeps its session cookie httpOnly. Its client exchanges that
  // session for a short-lived JWT that FastAPI can validate via Neon JWKS.
  if (config.url?.startsWith("/api/v1/")) {
    const session = await authClient.getSession();
    const token = session.data?.session?.token;
    if (token) {
      config.headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return config;
});

function errorMessage(data: unknown, fallback: string): { message: string; code?: string; requestId?: string } {
  if (typeof data === "object" && data && "error" in data) {
    const envelope = data.error;
    if (typeof envelope === "object" && envelope) {
      const record = envelope as Record<string, unknown>;
      return {
        message: typeof record.message === "string" ? record.message : fallback,
        code: typeof record.code === "string" ? record.code : undefined,
        requestId: typeof record.request_id === "string" ? record.request_id : undefined,
      };
    }
  }
  const detail = typeof data === "object" && data && "detail" in data ? data.detail : data;
  if (typeof detail === "string") return { message: detail };
  if (Array.isArray(detail)) {
    return { message: detail.map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item))).join("；") };
  }
  return { message: fallback };
}

export async function request<T>(operation: () => Promise<AxiosResponse<T>>): Promise<T> {
  try {
    const response = await operation();
    return response.data;
  } catch (error) {
    if (!axios.isAxiosError(error)) {
      throw new ApiClientError({ message: "發生未知錯誤。" });
    }

    const normalized = errorMessage(error.response?.data, error.message ?? "無法連線至服務。");
    throw new ApiClientError({
      ...normalized,
      status: error.response?.status,
    });
  }
}

export const apiClient = {
  health: () => request<HealthResponse>(() => http.get("/health")),
  joinMeeting: (payload: JoinMeetingRequest) => request<MeetingBotResponse>(() => http.post("/meetbot/join", payload)),
};
