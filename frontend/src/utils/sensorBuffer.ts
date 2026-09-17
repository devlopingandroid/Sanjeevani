/**
 * 30-Second Rolling Sensor Buffer & Feature Extraction
 * 
 * Manages an in-memory buffer of REAL backend sensor samples.
 * Automatically purges samples older than 30 seconds and deduplicates by sequence_number.
 * Strictly enforces NO-MOCK-DATA policy.
 */
import { LiveSensorSample } from '../services/sensorService';

export class RollingSensorBuffer {
  private samples: LiveSensorSample[] = [];
  private readonly maxAgeMs: number = 30000; // 30 seconds window

  /**
   * Adds new samples to the buffer, ensuring sequence deduplication and timestamp sorting.
   */
  public addSamples(newSamples: LiveSensorSample[]): void {
    const existingSeq = new Set(
      this.samples
        .map((s) => s.sequence_number)
        .filter((seq): seq is number => seq !== null && seq !== undefined)
    );

    for (const sample of newSamples) {
      if (
        sample.sequence_number !== null &&
        sample.sequence_number !== undefined &&
        existingSeq.has(sample.sequence_number)
      ) {
        continue;
      }
      this.samples.push(sample);
      if (sample.sequence_number !== null && sample.sequence_number !== undefined) {
        existingSeq.add(sample.sequence_number);
      }
    }

    this.purgeStale();
  }

  /**
   * Removes samples older than 30 seconds.
   */
  public purgeStale(): void {
    const now = Date.now();
    this.samples = this.samples.filter((s) => {
      const ts = s.sensor_timestamp || s.received_at;
      if (!ts) return false;
      const sampleTime = new Date(ts).getTime();
      return !isNaN(sampleTime) && now - sampleTime <= this.maxAgeMs;
    });

    // Sort by sequence number or timestamp ascending
    this.samples.sort((a, b) => {
      if (a.sequence_number != null && b.sequence_number != null) {
        return a.sequence_number - b.sequence_number;
      }
      return new Date(a.sensor_timestamp).getTime() - new Date(b.sensor_timestamp).getTime();
    });
  }

  /**
   * Returns current buffer sample count.
   */
  public getCount(): number {
    this.purgeStale();
    return this.samples.length;
  }

  /**
   * Returns copy of current 30s buffer samples.
   */
  public getSamples(): LiveSensorSample[] {
    this.purgeStale();
    return [...this.samples];
  }

  /**
   * Extracts current physiological vitals snapshot from the 30s buffer.
   */
  public extractVitalsSnapshot() {
    this.purgeStale();
    if (this.samples.length === 0) {
      return null;
    }

    const latest = this.samples[this.samples.length - 1];

    // 1. Valid Heart Rate (BPM)
    const validHrSamples = this.samples.filter(
      (s) => s.valid_heart_rate === 1 && s.heart_rate != null && s.heart_rate > 30 && s.heart_rate < 220
    );
    const hr = validHrSamples.length > 0
      ? validHrSamples[validHrSamples.length - 1].heart_rate!
      : (latest.heart_rate && latest.heart_rate > 30 ? latest.heart_rate : null);

    // 2. Valid SpO2 (%)
    const validSpo2Samples = this.samples.filter(
      (s) => s.valid_spo2 === 1 && s.spo2 != null && s.spo2 >= 70 && s.spo2 <= 100
    );
    const spo2 = validSpo2Samples.length > 0
      ? validSpo2Samples[validSpo2Samples.length - 1].spo2!
      : (latest.spo2 && latest.spo2 >= 70 ? latest.spo2 : null);

    // 3. Skin Temperature (°F)
    const tempF = latest.temperature && latest.temperature > 60 && latest.temperature < 120
      ? latest.temperature
      : null;

    // 4. Skin Conductance (uS) estimated from GSR voltage / raw
    const rawGsr = (latest as any).gsr_raw ?? (latest as any).GSR_Raw ?? 0;
    const gsrVoltage = (latest as any).gsr_voltage ?? (latest as any).GSR_Voltage ?? (rawGsr > 0 ? (rawGsr / 4095.0) * 3.3 : 0);
    const skinConductanceUs = gsrVoltage > 0 ? Number(((gsrVoltage / 3.3) * 10.0).toFixed(2)) : 0;

    // 5. Motion Magnitude (Units)
    const ax = latest.accel_x ?? 0;
    const ay = latest.accel_y ?? 0;
    const az = latest.accel_z ?? 0;
    const motionMagnitude = Number(Math.sqrt(ax * ax + ay * ay + az * az).toFixed(2));

    return {
      heart_rate_bpm: hr,
      spo2,
      temperature_f: tempF,
      skin_conductance_us: skinConductanceUs,
      motion_magnitude: motionMagnitude,
      last_updated: latest.received_at || latest.sensor_timestamp,
      sequence_number: latest.sequence_number,
    };
  }

  /**
   * Clears all buffer samples.
   */
  public clear(): void {
    this.samples = [];
  }
}

export const sensorBuffer = new RollingSensorBuffer();
