/**
 * Stress Service
 * 
 * Fetches latest verified stress inference or triggers real-time 30s evaluation.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import { StressPredictionResponse } from '../api/types';

export const stressService = {
  async getLatest(deviceId: string): Promise<StressPredictionResponse> {
    return apiRequest<StressPredictionResponse>(ENDPOINTS.STRESS.LATEST(deviceId));
  },

  async triggerPredict(deviceId: string): Promise<StressPredictionResponse> {
    return apiRequest<StressPredictionResponse>(ENDPOINTS.STRESS.PREDICT, {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId }),
    });
  },
};
