import axios, { type AxiosResponse } from "axios";
import type { ApiError, HealthResponse, JoinMeetingRequest, MeetingBotResponse } from "../../types/api";

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
  withCredentials: true,
  headers: { Accept: "application/json" },
});

let tokenRequest: Promise<string> | null = null;

async function getToken(): Promise<string> {
  if (tokenRequest) return tokenRequest;
  tokenRequest = (async () => {
    let response: Response;
    try {
      response = await fetch("/api/auth/token", {
        credentials: "include", cache: "no-store", signal: AbortSignal.timeout(10_000),
      });
    } catch {
      throw new ApiClientError({ status: 503, message: "登入驗證服務暫時無法連線，請稍後重試。" });
    }
    if (!response.ok) {
      throw new ApiClientError({ status: response.status, message: response.status === 401
        ? "登入已失效，請重新登入。" : "登入驗證服務暫時無法使用，請稍後重試。" });
    }
    const payload: unknown = await response.json();
    if (!payload || typeof payload !== "object" || !("token" in payload)
        || typeof payload.token !== "string" || !payload.token) {
      throw new ApiClientError({ status: 401, message: "無法取得登入憑證，請重新登入。" });
    }
    return payload.token;
  })();
  try {
    return await tokenRequest;
  } finally {
    tokenRequest = null;
  }
}

http.interceptors.request.use(async (config) => {
  // Neon Auth keeps its session cookie httpOnly. Its client exchanges that
  // session for a short-lived JWT that FastAPI can validate via Neon JWKS.
  if (config.url?.startsWith("/api/v1/")) {
    // The Next.js adapter exposes Better Auth's JWT endpoint through the local
    // auth proxy. The React session object itself does not contain a bearer JWT.
    const token = await getToken();
    config.headers.set("Authorization", `Bearer ${token}`);
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
    const response = await operation().catch(async (error: unknown) => {
      // Retry only idempotent reads, once. Never replay writes or authentication failures.
      if (axios.isAxiosError(error) && error.response?.status === 503
          && error.config?.method?.toLowerCase() === "get" && !error.config.signal?.aborted) {
        await new Promise((resolve) => setTimeout(resolve, 300));
        return http.request<T>(error.config);
      }
      throw error;
    });
    return response.data;
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    if (!axios.isAxiosError(error)) {
      throw new ApiClientError({ message: "發生未知錯誤。" });
    }

    const normalized = errorMessage(error.response?.data, error.message ?? "無法連線至服務。");
    if (error.response?.status === 401) {
      normalized.message = "需要驗證身分，請先登入；登入後請重新整理頁面。";
    } else if (error.response?.status === 403) {
      normalized.message = "你沒有權限查看這項資料，請切換到所屬工作區。";
    }
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
