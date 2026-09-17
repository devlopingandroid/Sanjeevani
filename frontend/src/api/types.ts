/**
 * SANJEEVNI API Types
 * 
 * Strict TypeScript types matching the backend Pydantic models.
 * Strictly adheres to the NO-MOCK-DATA contract.
 */

export enum DataStatus {
  REAL_DATA = 'REAL_DATA',
  DEMO_DATA = 'DEMO_DATA',
  NO_DATA = 'NO_DATA',
  INSUFFICIENT_DATA = 'INSUFFICIENT_DATA',
  DEVICE_DISCONNECTED = 'DEVICE_DISCONNECTED',
  SENSOR_ERROR = 'SENSOR_ERROR',
  MODEL_UNAVAILABLE = 'MODEL_UNAVAILABLE',
}

export enum DeviceStatus {
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  WAITING_FOR_DATA = 'WAITING_FOR_DATA',
  SENSOR_ERROR = 'SENSOR_ERROR',
  NO_DATA = 'NO_DATA',
}

export interface VitalsSnapshot {
  heart_rate_bpm: number | null;
  hrv_rmssd_ms: number | null;
  temperature_f: number | null;
  skin_conductance_us: number | null;
  motion_magnitude: number | null;
  spo2?: number | null;
  last_updated?: string | null;
}

export interface StressSnapshot {
  stress_level: 'BASELINE' | 'STRESS' | 'LOW' | 'MODERATE' | 'HIGH' | null;
  stress_score: number | null; // 0.0 - 100.0
  confidence: number | null;
  predicted_at?: string | null;
}

export interface DashboardSummaryResponse {
  device_id: string | null;
  device_status: DeviceStatus;
  data_status: DataStatus;
  last_seen: string | null;
  vitals: VitalsSnapshot | null;
  stress: StressSnapshot | null;
  message: string;
}

export interface StressPredictionResponse {
  device_id: string;
  data_status: DataStatus;
  stress_level: 'BASELINE' | 'STRESS' | string | null;
  stress_score: number | null;
  raw_probability: number | null;
  confidence: number | null;
  predicted_at: string | null;
  model_status: string;
  message: string;
  features_used_count: number;
  features_snapshot?: Record<string, number> | null;
}

export interface DeviceResponse {
  id: number;
  device_id: string;
  name: string;
  user_id?: string | null;
  firmware_version?: string | null;
  hardware_version?: string | null;
  status: DeviceStatus;
  registered_at: string;
  last_seen: string | null;
  last_packet_received_at?: string | null;
  last_valid_packet_at?: string | null;
  last_transport?: string | null;
  total_packets_received?: number;
  total_packets_accepted?: number;
  total_packets_rejected?: number;
  current_sampling_rate_hz?: number | null;
}

export interface VitalsHistoryRecord {
  timestamp: string;
  heart_rate_bpm: number | null;
  hrv_rmssd_ms: number | null;
  temperature_f: number | null;
  skin_conductance_us: number | null;
  motion_magnitude: number | null;
}

// --- Auth & User Types ---

export interface UserProfile {
  id: number;
  email: string;
  full_name: string | null;
  profile_image_url?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthStatusResponse {
  success: boolean;
  message: string;
}

// --- AI Chat Types ---

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface AIChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
  include_health_context?: boolean;
}

export interface AIChatResponse {
  reply: string;
  model: string;
  timestamp: string;
  health_context_included: boolean;
  status: string;
}
