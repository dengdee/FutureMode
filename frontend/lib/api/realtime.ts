import { http, request } from "./client";
import type { MeetingStateSnapshot, RealtimeEvent } from "../../types/api";

export class RealtimeEventAdapter {
  private readonly seen = new Set<string>();
  accept(value: unknown): RealtimeEvent | null {
    if (!value || typeof value !== "object") return null;
    const raw = value as Record<string, unknown>;
    const eventId = typeof raw.event_id === "string" ? raw.event_id : null;
    const meetingId =
      typeof raw.meeting_id === "string" ? raw.meeting_id : null;
    const eventType =
      typeof raw.event_type === "string" ? raw.event_type : null;
    if (!eventId || !meetingId || !eventType || this.seen.has(eventId))
      return null;
    this.seen.add(eventId);
    return {
      event_id: eventId,
      meeting_id: meetingId,
      timestamp:
        typeof raw.timestamp === "string"
          ? raw.timestamp
          : new Date().toISOString(),
      schema_version:
        typeof raw.schema_version === "string" ? raw.schema_version : "1",
      event_type: eventType,
      payload: raw.payload,
    };
  }
}

export function getMeetingState(meetingId: string) {
  return request<MeetingStateSnapshot>(() =>
    http.get(`/api/v1/meetings/${meetingId}/state`),
  );
}
