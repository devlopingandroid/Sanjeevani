import { describe, test, expect, beforeEach } from '@jest/globals';
import { sensorBuffer } from '../src/utils/sensorBuffer';

describe('SensorBuffer and Demo GSR Processing', () => {
  beforeEach(() => {
    sensorBuffer.clear();
  });

  test('processes sample with gsr_raw alias and calculates skin conductance', () => {
    const sample = {
      device_id: 'SANJEEVNI-ESP32-001',
      sensor_timestamp: new Date().toISOString(),
      sequence_number: 100,
      heart_rate: 72,
      valid_heart_rate: 1,
      spo2: 98,
      valid_spo2: 1,
      temperature: 98.6,
      gsr_raw: 2200,
      gsr_voltage: 1.7736,
      accel_x: 0,
      accel_y: 1,
      accel_z: 0,
      gyro_x: 0,
      gyro_y: 0,
      gyro_z: 0,
      ir: 20000,
      red: 100000,
    };

    sensorBuffer.addSamples([sample as any]);
    const snapshot = sensorBuffer.extractVitalsSnapshot();

    expect(snapshot).not.toBeNull();
    expect(snapshot!.skin_conductance_us).toBeGreaterThan(0);
    // 1.7736 / 3.3 * 10 = 5.3745 uS
    expect(snapshot!.skin_conductance_us).toBeCloseTo(5.37, 1);
  });

  test('processes sample with uppercase GSR_Raw / GSR_Voltage alias', () => {
    const sample = {
      device_id: 'SANJEEVNI-ESP32-001',
      sensor_timestamp: new Date().toISOString(),
      sequence_number: 101,
      heart_rate: 70,
      valid_heart_rate: 1,
      spo2: 97,
      valid_spo2: 1,
      temperature: 98.4,
      GSR_Raw: 2400,
      GSR_Voltage: 1.934,
      accel_x: 0,
      accel_y: 1,
      accel_z: 0,
      gyro_x: 0,
      gyro_y: 0,
      gyro_z: 0,
      ir: 20000,
      red: 100000,
    };

    sensorBuffer.addSamples([sample as any]);
    const snapshot = sensorBuffer.extractVitalsSnapshot();

    expect(snapshot).not.toBeNull();
    expect(snapshot!.skin_conductance_us).toBeGreaterThan(0);
    // 1.934 / 3.3 * 10 = 5.86 uS
    expect(snapshot!.skin_conductance_us).toBeCloseTo(5.86, 1);
  });

  test('bounded demo range 2000-2500 raw produces ~4.88-6.11 uS conductance', () => {
    // Test lower bound raw 2000 => voltage 1.6117 => ~4.88 uS
    const rawMin = 2000;
    const voltMin = (rawMin / 4095.0) * 3.3;
    sensorBuffer.addSamples([{
      device_id: 'SANJEEVNI-ESP32-001',
      sensor_timestamp: new Date().toISOString(),
      sequence_number: 102,
      gsr_raw: rawMin,
      gsr_voltage: voltMin,
      heart_rate: 70,
      valid_heart_rate: 1,
      spo2: 98,
      valid_spo2: 1,
      temperature: 98.0,
      accel_x: 0, accel_y: 1, accel_z: 0, gyro_x: 0, gyro_y: 0, gyro_z: 0, ir: 20000, red: 100000,
    } as any]);

    let snapshot = sensorBuffer.extractVitalsSnapshot();
    expect(snapshot!.skin_conductance_us).toBeGreaterThanOrEqual(4.8);
    expect(snapshot!.skin_conductance_us).toBeLessThanOrEqual(6.2);

    sensorBuffer.clear();

    // Test upper bound raw 2500 => voltage 2.0146 => ~6.11 uS
    const rawMax = 2500;
    const voltMax = (rawMax / 4095.0) * 3.3;
    sensorBuffer.addSamples([{
      device_id: 'SANJEEVNI-ESP32-001',
      sensor_timestamp: new Date().toISOString(),
      sequence_number: 103,
      gsr_raw: rawMax,
      gsr_voltage: voltMax,
      heart_rate: 70,
      valid_heart_rate: 1,
      spo2: 98,
      valid_spo2: 1,
      temperature: 98.0,
      accel_x: 0, accel_y: 1, accel_z: 0, gyro_x: 0, gyro_y: 0, gyro_z: 0, ir: 20000, red: 100000,
    } as any]);

    snapshot = sensorBuffer.extractVitalsSnapshot();
    expect(snapshot!.skin_conductance_us).toBeGreaterThanOrEqual(4.8);
    expect(snapshot!.skin_conductance_us).toBeLessThanOrEqual(6.2);
  });
});
