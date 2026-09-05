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
  display_name?: string | null;
  email?: string | null;
  claims?: Record<string, unknown>;
};

export type Team = {
  id: string;
  name: string;
  role: string;
};

export type TeamResponse = {
  teams: Team[];
};

export type TeamMember = {
  user_id: string;
  external_id: string;
  display_name: string;
  role: string;
};

export type TeamMemberResponse = {
  members: TeamMember[];
};
export type AddonAccessTokenResponse = { token: string; expires_at?: string; expiresIn?: number };
export type VoteChoice = "support" | "later" | "ignore";
export type LiveSnapshotResponse = {
  meeting?: MeetingSummary;
  state?: Record<string, unknown>;
  participants?: Array<Record<string, unknown>>;
  suggestions?: Array<Record<string, unknown>>;
  policy?: Record<string, unknown>;
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
export type ParticipantCreateResponse = { meeting_id: string; user_id: string; role: string };
export type AgendaItemCreateRequest = { position: number; title: string; description?: string | null };
export type AgendaItemUpdateRequest = { position?: number | null; title?: string | null; description?: string | null; status?: string | null };
export type AgendaItemCreateResponse = { id: string; meeting_id: string; position: number };

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

export type Transcript = { id: string; meeting_id: string; speaker_user_id: string | null; speaker_label: string | null; sequence: number; started_at: string | null; ended_at: string | null; text: string; source: string; confidence: number | null };
export type Consensus = { id: string; meeting_id: string; version: number; content: string; status: string; created_at: string };
export type ConsensusFeedback = { id: string; decision: string; comment: string | null; created_at: string };
export type ActionItem = { id: string; meeting_id: string; title: string; assignee_user_id: string | null; due_date: string | null; status: string };
export type Suggestion = { id: string; meeting_id: string; state_version: number; title: string; content: string; status: string; confidence: number | null; created_at: string };
export type DocumentSummary = { id: string; team_id: string; name: string; source_type: string; status: string };
export type DocumentSearchResult = { chunk_id: string; document_id: string; document_name: string; position: number; content: string; score: number };
export type PersonalMessage = { id: string; meeting_id: string; role: string; content: string; created_at: string };
