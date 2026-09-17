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
  conversation_id?: string;
  include_health_context?: boolean;
}

export interface AIChatResponse {
  reply: string;
  message?: string;
  conversation_id?: string;
  model: string;
  timestamp: string;
  health_context_included: boolean;
  status: string;
  scope?: string;
  handled_by?: string;
}

export interface ConversationRecord {
  id: string;
  user_id: number;
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageRecord {
  id: string;
  conversation_id: string;
  user_id: number;
  role: 'user' | 'assistant';
  message: string;
  created_at: string;
}

export interface PaginatedConversations {
  items: ConversationRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface PaginatedMessages {
  items: ChatMessageRecord[];
  total: number;
  limit: number;
  offset: number;
}


// --- Manual Model Testing Types ---

export interface ModelTestRequestPayload {
  eda_mean: number;
  eda_std: number;
  eda_min: number;
  eda_max: number;
  eda_range: number;
  eda_slope: number;
  scr_count: number;
  scr_mean: number;
  bvp_mean: number;
  bvp_std: number;
  bvp_min: number;
  bvp_max: number;
  bvp_range: number;
  bvp_hr: number;
  hr_mean: number;
  hr_std: number;
  hr_min: number;
  hr_max: number;
  acc_mean: number;
  acc_std: number;
  acc_min: number;
  acc_max: number;
  acc_range: number;
  acc_rms: number;
  temp_mean: number;
  temp_std: number;
}

export interface ModelTestResponsePayload {
  status: string; // "MODEL_TEST_SUCCESS"
  prediction: number; // 0 or 1
  stress_level: 'BASELINE' | 'STRESS' | string;
  stress_probability: number; // 0.0 - 1.0
  confidence: number;
  model_name: string;
  feature_count: number;
  threshold: number;
  message: string;
}

// --- Trusted Contact Types ---

export enum NotificationLevel {
  HIGH_AND_CRITICAL = 'high_and_critical',
  CRITICAL_ONLY = 'critical_only',
}

export interface TrustedContactRecord {
  id: string;
  user_id: number;
  name: string;
  phone_number: string;
  relationship: string | null;
  enabled: boolean;
  consent_given: boolean;
  notification_level: NotificationLevel;
  created_at: string;
  updated_at: string;
}

export interface TrustedContactCreatePayload {
  name: string;
  phone_number: string;
  relationship?: string | null;
  enabled?: boolean;
  consent_given: boolean;
  notification_level?: NotificationLevel;
}

export interface TrustedContactUpdatePayload {
  name?: string;
  phone_number?: string;
  relationship?: string | null;
  enabled?: boolean;
  consent_given?: boolean;
  notification_level?: NotificationLevel;
}

// --- Multimodal Wellness & Data Retention Types ---

export interface MultimodalWellnessResponse {
  user_id: number;
  conversation_id?: string | null;
  device_id?: string | null;
  physiological_stress_level?: 'BASELINE' | 'LOW' | 'MODERATE' | 'HIGH' | string | null;
  physiological_stress_score?: number | null;
  conversational_risk_level?: 'NORMAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL' | string | null;
  crisis_indicator: boolean;
  wellness_concern_level: 'normal_wellness' | 'elevated_concern' | 'high_concern' | 'critical_concern' | string;
  rule_applied: string;
  explanation: string;
  evaluated_at: string;
}

export interface EmotionalDataDeletionResponse {
  success: boolean;
  message: string;
  deleted_assessments_count: number;
  deleted_risk_events_count: number;
  deleted_notification_events_count: number;
}

// --- YouTube Exercise Video Types ---

export interface YouTubeVideoItem {
  video_id: string;
  title: string;
  description?: string;
  thumbnail_url: string;
  channel_title: string;
  published_at?: string | null;
  youtube_url: string;
}

export interface ExerciseVideosResponse {
  exercise: string;
  videos: YouTubeVideoItem[];
}



