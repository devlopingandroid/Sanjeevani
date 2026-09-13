import { describe, test, expect } from '@jest/globals';
import {
  formatBpm,
  formatMs,
  formatTempF,
  formatTempC,
  formatGSR,
  formatMotion,
  formatStressScore,
  formatStatusLabel,
} from '../src/utils/formatters';
import { DataStatus, DeviceStatus } from '../src/api/types';
import { ApiClientError } from '../src/api/client';

describe('Formatters & Honest State Verification', () => {
  test('returns "--" on null or undefined for all physiological values (NO FAKE DEFAULTS)', () => {
    expect(formatBpm(null)).toBe('--');
    expect(formatBpm(undefined)).toBe('--');
    expect(formatMs(null)).toBe('--');
    expect(formatMs(undefined)).toBe('--');
    expect(formatTempF(null)).toBe('--');
    expect(formatTempF(undefined)).toBe('--');
    expect(formatTempC(null)).toBe('--');
    expect(formatTempC(undefined)).toBe('--');
    expect(formatGSR(null)).toBe('--');
    expect(formatGSR(undefined)).toBe('--');
    expect(formatMotion(null)).toBe('--');
    expect(formatMotion(undefined)).toBe('--');
    expect(formatStressScore(null)).toBe('--');
    expect(formatStressScore(undefined)).toBe('--');
  });

  test('formats valid physiological numbers accurately', () => {
    expect(formatBpm(72.4)).toBe('72');
    expect(formatBpm(85.8)).toBe('86');
    expect(formatMs(42.3)).toBe('42');
    expect(formatTempF(98.6)).toBe('98.6°F');
    expect(formatTempC(98.6)).toBe('37.0°C');
    expect(formatGSR(2.456)).toBe('2.46 μS');
    expect(formatMotion(64.2)).toBe('64');
    expect(formatStressScore(42.1)).toBe('42%');
  });

  test('maps all explicit backend statuses to readable labels without faking active status', () => {
    expect(formatStatusLabel(DataStatus.REAL_DATA)).toBe('Connected');
    expect(formatStatusLabel(DataStatus.INSUFFICIENT_DATA)).toBe('Collecting Data');
    expect(formatStatusLabel(DataStatus.DEVICE_DISCONNECTED)).toBe('Disconnected');
    expect(formatStatusLabel(DataStatus.SENSOR_ERROR)).toBe('Sensor Lead-Off');
    expect(formatStatusLabel(DataStatus.MODEL_UNAVAILABLE)).toBe('Model Unavailable');
    expect(formatStatusLabel(DataStatus.NO_DATA)).toBe('No Data');
    expect(formatStatusLabel(DeviceStatus.WAITING_FOR_DATA)).toBe('Collecting Data');
  });
});

describe('API Client Error Hierarchy', () => {
  test('ApiClientError correctly captures status code and error message', () => {
    const error = new ApiClientError('Wearable device not found', 404, 'DEVICE_NOT_FOUND');
    expect(error.message).toBe('Wearable device not found');
    expect(error.statusCode).toBe(404);
    expect(error.errorCode).toBe('DEVICE_NOT_FOUND');
    expect(error.name).toBe('ApiClientError');
  });
});
