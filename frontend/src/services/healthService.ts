/**
 * Backend Health Service
 * 
 * Interacts with root health endpoints:
 * - GET /health/live (Liveness check: returns {"status": "alive", "timestamp": "...", "service": "sanjeevni-backend"})
 * - GET /health/ready (Readiness check: returns {"status": "ready", ...})
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';

export interface HealthLiveResponse {
  status: string; // "alive"
  timestamp?: string;
  service?: string; // "sanjeevni-backend"
}

export interface HealthReadyResponse {
  status: string; // "ready"
  timestamp?: string;
  service?: string;
  database?: string;
  model?: string;
}

export const healthService = {
  /**
   * Probes GET /health/live at root (NOT under /api/v1).
   * Returns HealthLiveResponse on HTTP 200.
   */
  async checkLiveHealth(): Promise<HealthLiveResponse> {
    return apiRequest<HealthLiveResponse>(ENDPOINTS.HEALTH.LIVENESS);
  },

  /**
   * Probes GET /health/ready at root.
   */
  async checkReadyHealth(): Promise<HealthReadyResponse> {
    return apiRequest<HealthReadyResponse>(ENDPOINTS.HEALTH.READINESS);
  },
};
