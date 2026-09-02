import { fetchApi, toCamelCase } from "./apiClient";
import type { CompaniesResponse } from "../../types/api";

export const companiesApi = {
  getCompanies: async (page: number = 1, pageSize: number = 25): Promise<CompaniesResponse> => {
    const rawData = await fetchApi<any>(`/api/dashboard/companies?page=${page}&page_size=${pageSize}`);
    return toCamelCase(rawData);
  },
};
