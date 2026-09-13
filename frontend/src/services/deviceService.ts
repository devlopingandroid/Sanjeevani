/**
 * Device Service
 * 
 * Manages registered ESP32 wearable hardware, packet metrics, and connectivity state.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import { DeviceResponse } from '../api/types';

export const deviceService = {
  async listDevices(): Promise<DeviceResponse[]> {
    return apiRequest<DeviceResponse[]>(ENDPOINTS.DEVICES.LIST);
  },

  async getDevice(deviceId: string): Promise<DeviceResponse> {
    return apiRequest<DeviceResponse>(ENDPOINTS.DEVICES.GET(deviceId));
  },

  async registerDevice(deviceId: string, name: string): Promise<DeviceResponse> {
    return apiRequest<DeviceResponse>(ENDPOINTS.DEVICES.REGISTER, {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId, name }),
    });
  },
};
