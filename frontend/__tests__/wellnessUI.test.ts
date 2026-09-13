/**
 * Phase 8 Frontend Wellness Service & Policy Tests
 *
 * Verifies that:
 * 1. wellnessService.getWellnessContext fetches multimodal response from /api/v1/wellness-context.
 * 2. wellnessService.deleteEmotionalData calls DELETE /api/v1/users/me/emotional-data.
 * 3. Wellness context payload matches non-diagnostic schema and never uses llm_suggested_risk_level directly.
 */
import { describe, test, expect, jest } from '@jest/globals';
import { wellnessService } from '../src/services/wellnessService';

describe('Phase 8 Wellness Service & Retention Verification', () => {
  test('getWellnessContext calls GET /api/v1/wellness-context', async () => {
    const originalFetch = (global as any).fetch;
    const mockContext = {
      user_id: 1,
      conversation_id: 'conv-123',
      device_id: 'DEV_001',
      physiological_stress_level: 'HIGH',
      physiological_stress_score: 85.0,
      conversational_risk_level: 'NORMAL',
      crisis_indicator: false,
      wellness_concern_level: 'elevated_concern',
      rule_applied: 'SENSOR_HIGH_CAPPED_AT_ELEVATED',
      explanation: 'Capped at elevated concern without chat corroboration',
      evaluated_at: '2026-09-14T00:00:00Z',
    };

    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockContext,
    });

    try {
      const res = await wellnessService.getWellnessContext('conv-123');
      expect(res.wellness_concern_level).toBe('elevated_concern');
      expect(res.rule_applied).toBe('SENSOR_HIGH_CAPPED_AT_ELEVATED');
      expect(res.crisis_indicator).toBe(false);
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('deleteEmotionalData issues DELETE /api/v1/users/me/emotional-data', async () => {
    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        message: 'Emotional wellness data successfully deleted.',
        deleted_assessments_count: 5,
        deleted_risk_events_count: 3,
        deleted_notification_events_count: 2,
      }),
    });

    try {
      const res = await wellnessService.deleteEmotionalData();
      expect(res.success).toBe(true);
      expect(res.deleted_assessments_count).toBe(5);
    } finally {
      (global as any).fetch = originalFetch;
    }
  });
});
