/**
 * SANJEEVNI API Client
 * 
 * Clean, lightweight fetch-based HTTP client with timeout,
 * JSON serialization, and structured error propagation.
 */
import { Platform } from 'react-native';

const getDefaultBaseUrl = (): string => {
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    return process.env.EXPO_PUBLIC_API_BASE_URL;
  }
  // Android emulator loops back to host via 10.0.2.2
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
};

export const API_BASE_URL = getDefaultBaseUrl();

export interface ApiErrorResponse {
  message: string;
  statusCode: number;
  errorCode?: string;
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public errorCode?: string
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = 8000
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      let errorCode: string | undefined;

      try {
        const errorData = await response.json();
        if (errorData?.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          } else if (errorData.detail.message) {
            errorMessage = errorData.detail.message;
            errorCode = errorData.detail.error_code;
          }
        } else if (errorData?.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Response body was not JSON
      }

      throw new ApiClientError(errorMessage, response.status, errorCode);
    }

    // Parse JSON
    return (await response.json()) as T;
  } catch (err: any) {
    clearTimeout(timer);
    if (err.name === 'AbortError') {
      throw new ApiClientError(`Request timeout after ${timeoutMs / 1000}s to ${endpoint}`, 408);
    }
    if (err instanceof ApiClientError) {
      throw err;
    }
    throw new ApiClientError(
      err.message || 'Unable to connect to Sanjeevni backend. Please check network connection.',
      0
    );
  }
}
