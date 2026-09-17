/**
 * Health Data Context
 * 
 * Central state provider managing live wearable telemetry, active device selection,
 * 30-second rolling sensor buffering, real-time polling, and ML stress inference.
 * Strictly adheres to the NO-MOCK-DATA policy.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';
import { deviceService } from '../services/deviceService';
import { stressService } from '../services/stressService';
import { sensorService } from '../services/sensorService';
import { healthService } from '../services/healthService';
import { sensorBuffer } from '../utils/sensorBuffer';
import { API_BASE_URL } from '../api/client';
import { CANONICAL_DEVICE_ID, ENDPOINTS } from '../api/endpoints';
import {
  DashboardSummaryResponse,
  DeviceResponse,
  StressPredictionResponse,
  DataStatus,
  DeviceStatus,
  VitalsSnapshot,
} from '../api/types';

interface HealthDataContextType {
  // State
  activeDeviceId: string;
  devices: DeviceResponse[];
  summary: DashboardSummaryResponse | null;
  latestStress: StressPredictionResponse | null;
  bufferSampleCount: number;
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;

  // Actions
  setActiveDeviceId: (id: string) => void;
  refreshData: () => Promise<void>;
  triggerStressEvaluation: () => Promise<StressPredictionResponse | null>;
}

const HealthDataContext = createContext<HealthDataContextType | undefined>(undefined);

export const HealthDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeDeviceId, setActiveDeviceId] = useState<string>(CANONICAL_DEVICE_ID);
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [latestStress, setLatestStress] = useState<StressPredictionResponse | null>(null);
  const [bufferSampleCount, setBufferSampleCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load available devices from backend
  const fetchDevices = useCallback(async () => {
    try {
      const devList = await deviceService.listDevices();
      setDevices(devList);
      // Prefer real physical wearable device 'SANJEEVNI-ESP32-001'
      const esp32Device = devList.find(d => d.device_id === CANONICAL_DEVICE_ID);
      if (esp32Device) {
        setActiveDeviceId(esp32Device.device_id);
      } else {
        setActiveDeviceId(CANONICAL_DEVICE_ID);
      }
    } catch (err: any) {
      setActiveDeviceId(CANONICAL_DEVICE_ID);
    }
  }, []);

  // Fetch real-time telemetry from FastAPI live cache & dashboard summary
  const fetchData = useCallback(async () => {
    setError(null);
    try {
      const targetDevId = CANONICAL_DEVICE_ID;

      // 1. Probe backend liveness via GET /health/live (root endpoint)
      let isBackendConnected = false;
      let healthRouteError: string | null = null;

      try {
        const healthRes = await healthService.checkLiveHealth();
        if (healthRes && (healthRes.status === 'alive' || healthRes.status === 'ok' || healthRes.status)) {
          isBackendConnected = true;
          console.log(`[HEALTH_CHECK] /health/live HTTP 200 OK -> status=${healthRes.status}, service=${healthRes.service || 'sanjeevni-backend'}`);
        }
      } catch (healthErr: any) {
        if (healthErr?.statusCode === 404) {
          healthRouteError = 'HTTP 404 Route Not Found on /health/live';
          console.warn(`[HEALTH_CHECK] ${healthRouteError}`);
        } else {
          console.warn(`[HEALTH_CHECK] Health probe failed: ${healthErr?.message || healthErr}`);
        }
      }

      // 2. Fetch dashboard summary & latest live memory sample concurrently
      const [summaryData, latestRes] = await Promise.all([
        dashboardService.getSummary(targetDevId).catch(() => null),
        sensorService.getLatest(targetDevId).catch(() => null),
      ]);

      if (summaryData || latestRes) {
        isBackendConnected = true;
      }

      console.log(`[BACKEND_URL] ${API_BASE_URL} (Connected: ${isBackendConnected})`);

      if (latestRes?.connected && latestRes.sample) {
        const sample = latestRes.sample;

        console.log(`[TELEMETRY_CONNECTION] CONNECTED -> device=${sample.device_id}`);
        console.log(`[TELEMETRY_RECEIVED] seq=${sample.sequence_number} hr=${sample.heart_rate} temp=${sample.temperature}`);

        // Add single sample to 30s rolling buffer
        sensorBuffer.addSamples([sample]);

        // Also fetch recent 30s history window if buffer is low
        if (sensorBuffer.getCount() < 10) {
          try {
            const histRes = await sensorService.getLiveHistory(targetDevId, 50);
            if (histRes.samples && histRes.samples.length > 0) {
              sensorBuffer.addSamples(histRes.samples);
            }
          } catch {}
        }

        const bufCount = sensorBuffer.getCount();
        setBufferSampleCount(bufCount);
        console.log(`[BUFFER_SIZE] ${bufCount} samples in 30s window`);

        const vitalsExtracted = sensorBuffer.extractVitalsSnapshot();

        const vitalsSnapshot: VitalsSnapshot = {
          heart_rate_bpm: vitalsExtracted?.heart_rate_bpm ?? (summaryData?.vitals?.heart_rate_bpm || sample.heart_rate || null),
          hrv_rmssd_ms: summaryData?.vitals?.hrv_rmssd_ms || null,
          temperature_f: vitalsExtracted?.temperature_f ?? (summaryData?.vitals?.temperature_f || sample.temperature || null),
          skin_conductance_us: vitalsExtracted?.skin_conductance_us ?? (summaryData?.vitals?.skin_conductance_us || null),
          motion_magnitude: vitalsExtracted?.motion_magnitude ?? (summaryData?.vitals?.motion_magnitude || null),
          spo2: sample.spo2 ?? summaryData?.vitals?.spo2 ?? null,
          last_updated: sample.received_at || sample.sensor_timestamp,
        };

        setSummary({
          device_id: sample.device_id,
          device_status: DeviceStatus.CONNECTED,
          data_status: DataStatus.REAL_DATA,
          last_seen: sample.received_at,
          vitals: vitalsSnapshot,
          stress: summaryData?.stress || summary?.stress || null,
          message: 'Streaming live wearable telemetry.',
        });

        // Try fetching latest verified stress prediction if available
        try {
          const stressData = await stressService.getLatest(sample.device_id);
          if (stressData) {
            setLatestStress(stressData);
          }
        } catch {}
      } else if (summaryData) {
        setSummary(summaryData);
        if (summaryData.device_id && summaryData.device_id === CANONICAL_DEVICE_ID) {
          setActiveDeviceId(summaryData.device_id);
        }
      } else if (isBackendConnected) {
        // Backend server is alive and reachable, but waiting for ESP32 sensor telemetry
        setSummary({
          device_id: targetDevId,
          device_status: DeviceStatus.WAITING_FOR_DATA,
          data_status: DataStatus.NO_DATA,
          last_seen: null,
          vitals: null,
          stress: null,
          message: `Backend connected (${API_BASE_URL}). Waiting for wearable telemetry...`,
        });
      } else {
        const errMsg = healthRouteError
          ? `Backend route error: ${healthRouteError}`
          : 'Backend server unreachable. Please verify connection.';
        throw new Error(errMsg);
      }
    } catch (err: any) {
      const errMsg = err.message || 'Unable to connect to Sanjeevni backend';
      console.warn(`[TELEMETRY_CONNECTION] DISCONNECTED -> ${errMsg}`);
      setError(errMsg);
      setSummary({
        device_id: activeDeviceId || 'SANJEEVNI-ESP32-001',
        device_status: DeviceStatus.DISCONNECTED,
        data_status: DataStatus.DEVICE_DISCONNECTED,
        last_seen: null,
        vitals: null,
        stress: null,
        message: errMsg,
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [activeDeviceId, summary?.stress]);

  // Initial load
  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // High-frequency live polling (every 1.5s) to reflect live ESP32 telemetry
  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetchData();
    }, 1500);
    return () => clearInterval(interval);
  }, [fetchData]);

  const refreshData = async () => {
    setIsRefreshing(true);
    await fetchDevices();
    await fetchData();
  };

  const triggerStressEvaluation = async (): Promise<StressPredictionResponse | null> => {
    const devId = activeDeviceId || summary?.device_id || 'SANJEEVNI-ESP32-001';
    try {
      console.log(`[MODEL_INPUT] Triggering 30s ML inference for device=${devId} with ${sensorBuffer.getCount()} samples`);
      const result = await stressService.triggerPredict(devId);
      console.log(`[MODEL_OUTPUT] Stress Prediction=${result.stress_level} Score=${result.stress_score}% Confidence=${result.confidence}`);
      setLatestStress(result);
      await fetchData();
      return result;
    } catch (err: any) {
      setError(err.message || 'Stress evaluation failed');
      return null;
    }
  };

  return (
    <HealthDataContext.Provider
      value={{
        activeDeviceId,
        devices,
        summary,
        latestStress,
        bufferSampleCount,
        isLoading,
        isRefreshing,
        error,
        setActiveDeviceId,
        refreshData,
        triggerStressEvaluation,
      }}
    >
      {children}
    </HealthDataContext.Provider>
  );
};

export const useHealthData = (): HealthDataContextType => {
  const context = useContext(HealthDataContext);
  if (!context) {
    throw new Error('useHealthData must be used within a HealthDataProvider');
  }
  return context;
};
