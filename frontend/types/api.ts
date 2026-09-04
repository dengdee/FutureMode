export type HealthResponse = {
  status: "ok" | string;
  environment: string;
};

export type ApiError = {
  message: string;
  status?: number;
};

export type JoinMeetingRequest = {
  meetingUrl: string;
};

export type MeetingBotResponse = {
  id: string;
  status: string;
};
