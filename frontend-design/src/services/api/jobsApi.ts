import { fetchApi, toCamelCase } from './apiClient';
import type { RawPaginatedResponse, RawJobResponse, PaginatedResponse, Job } from '../../types/api';

export const jobsApi = {
  getJobs: async (page = 1, pageSize = 50): Promise<PaginatedResponse<Job>> => {
    const rawData = await fetchApi<RawPaginatedResponse<RawJobResponse>>(`/api/dashboard/jobs?page=${page}&page_size=${pageSize}`);
    return toCamelCase(rawData);
  }
};
