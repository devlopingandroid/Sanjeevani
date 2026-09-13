/**
 * Dashboard Service
 * 
 * Interacts with /api/v1/dashboard/summary to retrieve real vitals and estimated stress.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import { DashboardSummaryResponse } from '../api/types';

export const dashboardService = {
  async getSummary(deviceId?: string): Promise<DashboardSummaryResponse> {
    const url = deviceId
      ? `${ENDPOINTS.DASHBOARD.SUMMARY}?device_id=${encodeURIComponent(deviceId)}`
      : ENDPOINTS.DASHBOARD.SUMMARY;
    return apiRequest<DashboardSummaryResponse>(url);
  },
};
