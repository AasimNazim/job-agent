export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

const getErrorMessage = (status: number): string => {
  switch (status) {
    case 400: return 'Bad request. Please check your input.';
    case 401: return 'Unauthorized. Please check your credentials.';
    case 403: return 'Forbidden. You do not have access to this resource.';
    case 404: return 'Resource not found.';
    case 422: return 'Unprocessable entity. Validation failed.';
    case 429: return 'Too many requests. Please slow down and try again.';
    case 500: return 'Internal server error. Unable to load data.';
    case 503: return 'Service unavailable. Please try again later.';
    default: return 'An unexpected error occurred while fetching data.';
  }
};

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const token = localStorage.getItem("dashboard_token");
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options?.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if ((response.status === 401 || response.status === 403) && token) {
        // Trigger a custom event so the App can route to login if valid token expired/invalid
        window.dispatchEvent(new Event('auth_error'));
      }
      throw new ApiError(response.status, getErrorMessage(response.status));
    }

    // Attempt to parse JSON, if it fails return empty object or throw
    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Handle network errors (e.g. CORS or backend down)
    throw new ApiError(500, 'Unable to connect to the server. Please try again.');
  }
}

// Utility to convert snake_case object to camelCase object
export function toCamelCase(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(v => toCamelCase(v));
  } else if (obj !== null && obj !== undefined && obj.constructor === Object) {
    return Object.keys(obj).reduce(
      (result, key) => {
        const camelKey = key.replace(/([-_][a-z])/ig, ($1) => {
          return $1.toUpperCase().replace('-', '').replace('_', '');
        });
        result[camelKey] = toCamelCase(obj[key]);
        return result;
      },
      {} as any
    );
  }
  return obj;
}
