/**
 * History Service
 * 
 * Fetches real historical sensor and vitals telemetry.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import { VitalsHistoryRecord } from '../api/types';

export const historyService = {
  async getVitalsHistory(deviceId: string, limit: number = 50): Promise<VitalsHistoryRecord[]> {
    return apiRequest<VitalsHistoryRecord[]>(
      `${ENDPOINTS.HISTORY.VITALS(deviceId)}?limit=${limit}`
    );
  },
};
