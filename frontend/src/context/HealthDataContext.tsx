/**
 * Health Data Context
 * 
 * Central state provider managing live wearable data, active device selection,
 * real-time polling, and manual pull-to-refresh.
 * Strictly adheres to the NO-MOCK-DATA policy.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';
import { deviceService } from '../services/deviceService';
import { stressService } from '../services/stressService';
import {
  DashboardSummaryResponse,
  DeviceResponse,
  StressPredictionResponse,
  DataStatus,
  DeviceStatus,
} from '../api/types';

interface HealthDataContextType {
  // State
  activeDeviceId: string | null;
  devices: DeviceResponse[];
  summary: DashboardSummaryResponse | null;
  latestStress: StressPredictionResponse | null;
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
  const [activeDeviceId, setActiveDeviceId] = useState<string | null>(null);
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [latestStress, setLatestStress] = useState<StressPredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load available devices from backend
  const fetchDevices = useCallback(async () => {
    try {
      const devList = await deviceService.listDevices();
      setDevices(devList);
      if (devList.length > 0 && !activeDeviceId) {
        // Default to first registered device
        setActiveDeviceId(devList[0].device_id);
      }
    } catch {
      // Backend might be starting or device table empty
    }
  }, [activeDeviceId]);

  // Fetch summary and stress predictions for the active device
  const fetchData = useCallback(async () => {
    setError(null);
    try {
      const summaryData = await dashboardService.getSummary(activeDeviceId || undefined);
      setSummary(summaryData);

      if (summaryData.device_id) {
        try {
          const stressData = await stressService.getLatest(summaryData.device_id);
          setLatestStress(stressData);
        } catch {
          // No stress prediction yet for this device
        }
      }
    } catch (err: any) {
      setError(err.message || 'Unable to connect to Sanjeevni backend');
      // If error occurs, create clean fallback state reflecting disconnected backend
      setSummary({
        device_id: activeDeviceId,
        device_status: DeviceStatus.DISCONNECTED,
        data_status: DataStatus.DEVICE_DISCONNECTED,
        last_seen: null,
        vitals: null,
        stress: null,
        message: 'Backend server unreachable. Please verify connection.',
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [activeDeviceId]);

  // Initial load
  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  useEffect(() => {
    fetchData();
    // Real-time polling every 6 seconds to track real telemetry stream
    const interval = setInterval(() => {
      fetchData();
    }, 6000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const refreshData = async () => {
    setIsRefreshing(true);
    await fetchDevices();
    await fetchData();
  };

  const triggerStressEvaluation = async (): Promise<StressPredictionResponse | null> => {
    if (!activeDeviceId) return null;
    try {
      const result = await stressService.triggerPredict(activeDeviceId);
      setLatestStress(result);
      // Refresh dashboard summary to sync
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
