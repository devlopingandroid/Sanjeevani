/**
 * SANJEEVNI API Endpoints
 * 
 * Maps directly to backend FastAPI routes.
 */

export const CANONICAL_DEVICE_ID = 'SANJEEVNI-ESP32-001';

export const ENDPOINTS = {
  HEALTH: {
    ROOT: '/',
    LIVENESS: '/health/live',
    READINESS: '/health/ready',
  },
  DASHBOARD: {
    SUMMARY: '/api/v1/dashboard/summary',
  },
  STRESS: {
    LATEST: (deviceId: string) => `/api/v1/stress/latest/${encodeURIComponent(deviceId)}`,
    PREDICT: '/api/v1/stress/predict',
    MODEL_TEST: '/api/v1/stress/model-test',
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
    EMOTIONAL_DATA: '/api/v1/users/me/emotional-data',
  },
  AI: {
    CHAT: '/api/v1/ai/chat',
  },
  CONVERSATIONS: {
    LIST: '/api/v1/conversations',
    CREATE: '/api/v1/conversations',
    GET: (id: string) => `/api/v1/conversations/${encodeURIComponent(id)}`,
    DELETE: (id: string) => `/api/v1/conversations/${encodeURIComponent(id)}`,
    MESSAGES: (id: string) => `/api/v1/conversations/${encodeURIComponent(id)}/messages`,
  },
  TRUSTED_CONTACT: {
    BASE: '/api/v1/trusted-contact',
  },
  WELLNESS: {
    CONTEXT: '/api/v1/wellness-context',
    EXERCISE_VIDEOS: (exerciseName: string) => `/api/v1/wellness/exercises/${encodeURIComponent(exerciseName)}/videos`,
  },
  SENSORS: {
    LATEST: (deviceId?: string) =>
      deviceId ? `/api/v1/sensors/latest/${encodeURIComponent(deviceId)}` : '/api/v1/sensors/latest',
    LIVE_HISTORY: (deviceId: string, limit = 100) =>
      `/api/v1/sensors/live/${encodeURIComponent(deviceId)}?limit=${limit}`,
    INGEST: '/api/v1/sensors/ingest',
  },
} as const;

