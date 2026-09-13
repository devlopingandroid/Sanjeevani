/**
 * SANJEEVNI API Client
 * 
 * Clean, lightweight fetch-based HTTP client with timeout,
 * JSON serialization, structured error propagation, and automatic
 * Authorization header attachment via storageService.
 * 
 * Dynamic Base URL Resolution:
 * 1. Explicit EXPO_PUBLIC_API_BASE_URL (from frontend/.env).
 * 2. If running inside Expo Go / dev client, auto-resolves the Metro host IP (e.g. 192.168.1.3:8000).
 * 3. Fallbacks: Android emulator -> 10.0.2.2:8000, iOS simulator / Web -> localhost:8000.
 */
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { storageService } from '../services/storageService';

const getDefaultBaseUrl = (): string => {
  // 1. Explicit environment configuration
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    return process.env.EXPO_PUBLIC_API_BASE_URL;
  }

  // 2. Auto-detect host IP from Expo Metro server (e.g., "192.168.1.3:8081" -> "192.168.1.3:8000")
  const hostUri = Constants.expoConfig?.hostUri || (Constants as any).manifest2?.extra?.expoGo?.debuggerHost;
  if (hostUri) {
    const hostIp = hostUri.split(':')[0];
    if (hostIp && hostIp !== 'localhost' && hostIp !== '127.0.0.1') {
      return `http://${hostIp}:8000`;
    }
  }

  // 3. Android Emulator fallback
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  // 4. iOS Simulator / Web / Desktop fallback
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

// Callback for global session expiration handling
let onUnauthorizedCallback: (() => void) | null = null;

export function registerUnauthorizedHandler(callback: () => void) {
  onUnauthorizedCallback = callback;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = 8000
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  // Retrieve JWT if present
  const token = await storageService.getToken();

  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
      // 401 Unauthorized handling
      if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
        if (onUnauthorizedCallback) {
          onUnauthorizedCallback();
        }
      }

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
          errorCode = errorData.error_code;
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
