export type HealthResponse = {
  status: "ok" | string;
  environment: string;
};

export type ApiError = {
  message: string;
  status?: number;
};

export type JoinMeetingRequest = {
  meeting_url: string;
};

export type MeetingBotResponse = Record<string, unknown>;

export type UserResponse = Record<string, unknown>;
export type AddonAccessTokenResponse = { token: string; expires_at?: string; expiresIn?: number };
export type VoteChoice = "support" | "later" | "ignore";
export type LiveSnapshotResponse = {
  meeting?: MeetingSummary;
  state?: Record<string, unknown>;
  participants?: Array<Record<string, unknown>>;
  suggestions?: Array<Record<string, unknown>>;
  policy?: Record<string, unknown>;
};
export type TeamResponse = Record<string, unknown>;
export type TeamMemberResponse = Record<string, unknown>;

export type MeetingSummary = {
  id: string;
  team_id: string;
  title: string;
  scheduled_at: string | null;
  status: string;
  ai_intervention_level: string;
};

export type MeetingCreateRequest = {
  team_id: string;
  title: string;
  scheduled_at?: string | null;
  ai_intervention_level?: string;
};

export type MeetingUpdateRequest = {
  title?: string | null;
  scheduled_at?: string | null;
  ai_intervention_level?: string | null;
};

export type ParticipantAddRequest = { user_id: string; role?: string };
export type ParticipantUpdateRequest = { role?: string | null; attendance_status?: string | null };
export type AgendaItemCreateRequest = { position: number; title: string; description?: string | null };
export type AgendaItemUpdateRequest = { position?: number | null; title?: string | null; description?: string | null; status?: string | null };
export type ParticipantResponse = Record<string, unknown>;
export type AgendaItemResponse = Record<string, unknown>;
