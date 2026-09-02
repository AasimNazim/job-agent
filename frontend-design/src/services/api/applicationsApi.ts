import { fetchApi, toCamelCase } from './apiClient';
import type { RawPaginatedResponse, RawApplicationResponse, PaginatedResponse, Application } from '../../types/api';

export const applicationsApi = {
  getApplications: async (page = 1, pageSize = 50): Promise<PaginatedResponse<Application>> => {
    const rawData = await fetchApi<RawPaginatedResponse<RawApplicationResponse>>(`/api/dashboard/applications?page=${page}&page_size=${pageSize}`);
    return toCamelCase(rawData);
  }
};
