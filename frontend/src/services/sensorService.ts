/**
 * Sensor Telemetry Service
 * 
 * Interacts with FastAPI backend live sensor endpoints:
 * - GET /api/v1/sensors/latest/{device_id}
 * - GET /api/v1/sensors/live/{device_id}?limit=100
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';

export interface LiveSensorSample {
  device_id: string;
  sensor_timestamp: string;
  received_at: string;
  sequence_number?: number | null;
  heart_rate?: number | null;
  valid_heart_rate?: number | null;
  spo2?: number | null;
  valid_spo2?: number | null;
  ir: number;
  red: number;
  accel_x: number;
  accel_y: number;
  accel_z: number;
  gyro_x: number;
  gyro_y: number;
  gyro_z: number;
  temperature: number;
  gsr_raw: number;
  gsr_voltage: number;
  transport?: string;
  quality?: string;
}

export interface LatestSensorResponse {
  device_id: string | null;
  connected: boolean;
  source: string;
  sample: LiveSensorSample | null;
  last_received_at?: string | null;
  sequence_number?: number | null;
}

export interface LiveHistoryResponse {
  device_id: string;
  sample_count: number;
  samples: LiveSensorSample[];
}

export const sensorService = {
  async getLatest(deviceId?: string): Promise<LatestSensorResponse> {
    const url = ENDPOINTS.SENSORS.LATEST(deviceId);
    return apiRequest<LatestSensorResponse>(url);
  },

  async getLiveHistory(deviceId: string, limit = 100): Promise<LiveHistoryResponse> {
    const url = ENDPOINTS.SENSORS.LIVE_HISTORY(deviceId, limit);
    return apiRequest<LiveHistoryResponse>(url);
  },
};
