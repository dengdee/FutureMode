export type HealthResponse = {
  status: "ok" | string;
  environment: string;
};

export type ApiError = {
  message: string;
  status?: number;
  code?: string;
  requestId?: string;
};

export type ReadyResponse = {
  status: "ok" | "degraded" | string;
  environment: string;
  checks: {
    api?: string;
    database?: string;
    meeting_baas?: string;
  };
};

export type JoinMeetingRequest = {
  meeting_url: string;
};

export type MeetingBotResponse = Record<string, unknown>;

export type UserResponse = {
  id: string;
  claims: Record<string, unknown>;
};

export type Team = {
  id: string;
  name: string;
  role: string;
};

export type TeamResponse = {
  teams: Team[];
};

/** `external_id` is currently the only user identifier returned by the API. */
export type TeamMember = {
  external_id: string;
  display_name: string;
  role: string;
};

export type TeamMemberResponse = {
  members: TeamMember[];
};

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

export type Participant = {
  user_id: string;
  role: string;
  attendance_status: string;
};

export type ParticipantResponse = Participant;
export type ParticipantsResponse = {
  participants: Participant[];
};

export type AgendaItem = {
  id: string;
  meeting_id?: string;
  position: number;
  title: string;
  description: string | null;
  status: string;
};

export type AgendaItemResponse = AgendaItem;
export type AgendaItemsResponse = {
  items: AgendaItem[];
};
