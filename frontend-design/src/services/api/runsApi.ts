import { fetchApi, toCamelCase } from './apiClient';
import type { RawPaginatedResponse, RawRunResponse, PaginatedResponse, AgentRun } from '../../types/api';

export const runsApi = {
  getRuns: async (page = 1, pageSize = 50): Promise<PaginatedResponse<AgentRun>> => {
    const rawData = await fetchApi<RawPaginatedResponse<RawRunResponse>>(`/api/dashboard/runs?page=${page}&page_size=${pageSize}`);
    return toCamelCase(rawData);
  },
  
  getRunDetails: async (runUuid: string): Promise<AgentRun> => {
    const rawData = await fetchApi<RawRunResponse>(`/api/dashboard/runs/${runUuid}`);
    return toCamelCase(rawData);
  }
};
