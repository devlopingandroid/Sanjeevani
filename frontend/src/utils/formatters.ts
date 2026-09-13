/**
 * Utility Formatters
 * 
 * Clean, accessible display formatting for physiological values,
 * timestamps, and hardware states. Enforces honest missing states ("--").
 */
import { DataStatus, DeviceStatus } from '../api/types';

export function formatBpm(bpm: number | null | undefined): string {
  if (bpm === null || bpm === undefined || isNaN(bpm)) return '--';
  return `${Math.round(bpm)}`;
}

export function formatMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || isNaN(ms)) return '--';
  return `${Math.round(ms)}`;
}

export function formatTempF(f: number | null | undefined): string {
  if (f === null || f === undefined || isNaN(f)) return '--';
  return `${f.toFixed(1)}°F`;
}

export function formatTempC(f: number | null | undefined): string {
  if (f === null || f === undefined || isNaN(f)) return '--';
  const c = (f - 32) * (5 / 9);
  return `${c.toFixed(1)}°C`;
}

export function formatGSR(us: number | null | undefined): string {
  if (us === null || us === undefined || isNaN(us)) return '--';
  return `${us.toFixed(2)} μS`;
}

export function formatMotion(mag: number | null | undefined): string {
  if (mag === null || mag === undefined || isNaN(mag)) return '--';
  return `${Math.round(mag)}`;
}

export function formatStressScore(score: number | null | undefined): string {
  if (score === null || score === undefined || isNaN(score)) return '--';
  return `${Math.round(score)}%`;
}

export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return 'Never';
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSec < 5) return 'Just now';
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  } catch {
    return 'Invalid date';
  }
}

export function formatStatusLabel(status: DataStatus | DeviceStatus): string {
  switch (status) {
    case DataStatus.REAL_DATA:
    case DeviceStatus.CONNECTED:
      return 'Connected';
    case DataStatus.INSUFFICIENT_DATA:
    case DeviceStatus.WAITING_FOR_DATA:
      return 'Collecting Data';
    case DataStatus.DEVICE_DISCONNECTED:
    case DeviceStatus.DISCONNECTED:
      return 'Disconnected';
    case DataStatus.SENSOR_ERROR:
    case DeviceStatus.SENSOR_ERROR:
      return 'Sensor Lead-Off';
    case DataStatus.MODEL_UNAVAILABLE:
      return 'Model Unavailable';
    case DataStatus.NO_DATA:
    case DeviceStatus.NO_DATA:
    default:
      return 'No Data';
  }
}
