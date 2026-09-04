import { apiClient } from "../api/client";

export const systemRepository = {
  getHealth: () => apiClient.health(),
};
