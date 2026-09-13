/**
 * SANJEEVNI API Endpoints
 * 
 * Maps directly to backend FastAPI routes.
 */

export const ENDPOINTS = {
  HEALTH: {
    ROOT: '/',
    LIVENESS: '/health',
    READINESS: '/health/ready',
  },
  DASHBOARD: {
    SUMMARY: '/api/v1/dashboard/summary',
  },
  STRESS: {
    LATEST: (deviceId: string) => `/api/v1/stress/latest/${encodeURIComponent(deviceId)}`,
    PREDICT: '/api/v1/stress/predict',
  },
  DEVICES: {
    LIST: '/api/v1/devices/',
    GET: (deviceId: string) => `/api/v1/devices/${encodeURIComponent(deviceId)}`,
    REGISTER: '/api/v1/devices/',
    STATUS: (deviceId: string) => `/api/v1/devices/${encodeURIComponent(deviceId)}/status`,
  },
  HISTORY: {
    VITALS: (deviceId: string) => `/api/v1/history/vitals/${encodeURIComponent(deviceId)}`,
    RAW: (deviceId: string) => `/api/v1/history/raw/${encodeURIComponent(deviceId)}`,
  },
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    REFRESH: '/api/v1/auth/refresh',
    LOGOUT: '/api/v1/auth/logout',
    FORGOT_PASSWORD: '/api/v1/auth/forgot-password',
    RESET_PASSWORD: '/api/v1/auth/reset-password',
  },
  USERS: {
    ME: '/api/v1/users/me',
    AVATAR: '/api/v1/users/me/avatar',
  },
  AI: {
    CHAT: '/api/v1/ai/chat',
  },
} as const;
