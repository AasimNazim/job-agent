import { fetchApi, toCamelCase } from "./apiClient";
import type { AnalyticsResponse } from "../../types/api";

export const analyticsApi = {
  getAnalytics: async (range: "7d" | "30d" | "90d" = "7d"): Promise<AnalyticsResponse> => {
    const rawData = await fetchApi<any>(`/api/dashboard/analytics?range=${range}`);
    return toCamelCase(rawData);
  },
};
