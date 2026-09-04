import axios, { type AxiosResponse } from "axios";
import type { ApiError, HealthResponse, JoinMeetingRequest, MeetingBotResponse } from "../../types/api";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: { Accept: "application/json" },
});

export async function request<T>(operation: () => Promise<AxiosResponse<T>>): Promise<T> {
  try {
    const response = await operation();
    return response.data;
  } catch (error) {
    if (!axios.isAxiosError(error)) {
      throw { message: "發生未知錯誤。" } satisfies ApiError;
    }

    throw {
      message: error.response?.data?.detail ?? error.message ?? "無法連線至服務。",
      status: error.response?.status,
    } satisfies ApiError;
  }
}

export const apiClient = {
  health: () => request<HealthResponse>(() => http.get("/health")),
  joinMeeting: (payload: JoinMeetingRequest) => request<MeetingBotResponse>(() => http.post("/meetbot/join", payload)),
};
