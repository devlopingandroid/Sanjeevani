/**
 * SANJEEVNI API Client
 * 
 * Clean, lightweight fetch-based HTTP client with timeout,
 * JSON serialization, structured error propagation, and automatic
 * Authorization header attachment via storageService.
 * 
 * Dynamic Base URL Resolution:
 * Evaluated dynamically per request (or on module load):
 * 1. Explicit EXPO_PUBLIC_API_BASE_URL (from frontend/.env).
 * 2. If running inside Expo Go / dev client, auto-resolves the Metro host IP from Constants:
 *    - Constants.expoConfig?.hostUri
 *    - Constants.experienceUrl
 *    - Constants.manifest?.debuggerHost
 *    - Constants.manifest2?.extra?.expoGo?.debuggerHost
 * 3. Fallbacks: Android emulator -> 10.0.2.2:8000, iOS simulator / Web -> localhost:8000.
 */
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { storageService } from '../services/storageService';

export const getApiBaseUrl = (): string => {
  // 1. Explicit environment configuration
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    return process.env.EXPO_PUBLIC_API_BASE_URL.replace(/\/+$/, '');
  }

  // 2. Auto-detect host IP from Expo Metro server
  const hostUri =
    Constants.expoConfig?.hostUri ||
    (Constants as any).manifest?.debuggerHost ||
    (Constants as any).manifest2?.extra?.expoGo?.debuggerHost ||
    ((Constants as any).experienceUrl ? (Constants as any).experienceUrl.replace(/^exp:\/\//, '') : null);

  if (hostUri && typeof hostUri === 'string') {
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

export const API_BASE_URL = getApiBaseUrl();

// Diagnostic logging for development verification
const isDev = typeof __DEV__ !== 'undefined' ? __DEV__ : process.env.NODE_ENV !== 'production';
if (isDev) {
  console.log(`[API] Platform: ${Platform.OS}`);
  console.log(`[API] Base URL: ${API_BASE_URL}`);
}

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

async function uploadMultipartWithXHR<T>(
  url: string,
  formData: FormData,
  token?: string | null,
  method: string = 'POST',
  timeoutMs: number = 30000
): Promise<T> {
  const XHR = typeof XMLHttpRequest !== 'undefined' ? XMLHttpRequest : (global as any).XMLHttpRequest;

  if (!XHR) {
    // Fallback for node test environment (Jest) where native RN XMLHttpRequest is not present
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    const response = await fetch(url, {
      method,
      headers,
      body: formData,
    });
    return (await response.json()) as T;
  }

  return new Promise((resolve, reject) => {
    const xhr = new XHR();
    xhr.open(method.toUpperCase(), url);
    xhr.timeout = timeoutMs;

    xhr.setRequestHeader('Accept', 'application/json');
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }
    // DO NOT set Content-Type header manually. Native React Native XHR generates the boundary automatically.

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const responseData = JSON.parse(xhr.responseText);
          resolve(responseData as T);
        } catch {
          resolve(xhr.responseText as any);
        }
      } else {
        if (xhr.status === 401 && onUnauthorizedCallback) {
          onUnauthorizedCallback();
        }

        let errorMessage = `HTTP Error ${xhr.status}: ${xhr.statusText || 'Request failed'}`;
        let errorCode: string | undefined;

        try {
          const errorData = JSON.parse(xhr.responseText);
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
        } catch {}

        reject(new ApiClientError(errorMessage, xhr.status, errorCode));
      }
    };

    xhr.onerror = () => {
      reject(
        new ApiClientError(
          'Unable to connect to Sanjeevni backend. Please check network connection.',
          0
        )
      );
    };

    xhr.ontimeout = () => {
      reject(new ApiClientError(`Request timeout after ${timeoutMs / 1000}s`, 408));
    };

    xhr.send(formData as any);
  });
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = 8000
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;

  if (isDev) {
    console.log(`[API] Request -> ${options.method || 'GET'} ${url}`);
  }

  // Retrieve JWT if present
  const token = await storageService.getToken();

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

  // Use native React Native XMLHttpRequest for FormData to bypass Expo Winter fetch FormData compatibility issues
  if (isFormData) {
    return await uploadMultipartWithXHR<T>(
      url,
      options.body as FormData,
      token,
      options.method || 'POST',
      timeoutMs
    );
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

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
