import { fetchApi, toCamelCase } from './apiClient';
import type { RawOverviewResponse, RawSystemStatusResponse, DashboardOverview, SystemHealth } from '../../types/api';

export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverview> => {
    const rawData = await fetchApi<RawOverviewResponse>('/api/dashboard/overview');
    return toCamelCase(rawData);
  },
  
  getSystemHealth: async (): Promise<SystemHealth> => {
    const rawData = await fetchApi<RawSystemStatusResponse>('/api/dashboard/system');
    return toCamelCase(rawData);
  }
};
