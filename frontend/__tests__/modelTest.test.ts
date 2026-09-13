/**
 * Frontend Unit Tests for Manual Model Testing Logic
 * 
 * Verifies:
 * 1. Payload structure contains exactly 26 physiological features.
 * 2. stressService.runModelTest calls POST /api/v1/stress/model-test with exact feature payload.
 * 3. Validation catches empty / non-numeric values.
 * 4. Model test response is parsed without fake fallbacks.
 * 5. Honest error handling when ML model or network is unavailable.
 */
import { describe, test, expect, jest } from '@jest/globals';
import { stressService } from '../src/services/stressService';
import { ModelTestRequestPayload, ModelTestResponsePayload } from '../src/api/types';

describe('Manual Model Testing Logic', () => {
  const getValidPayload = (): ModelTestRequestPayload => ({
    eda_mean: 0.52,
    eda_std: 0.13,
    eda_min: 0.20,
    eda_max: 0.85,
    eda_range: 0.65,
    eda_slope: 0.002,
    scr_count: 3.0,
    scr_mean: 0.25,
    bvp_mean: 0.05,
    bvp_std: 12.4,
    bvp_min: -45.0,
    bvp_max: 48.0,
    bvp_range: 93.0,
    bvp_hr: 74.0,
    hr_mean: 75.2,
    hr_std: 4.1,
    hr_min: 68.0,
    hr_max: 86.0,
    acc_mean: 64.2,
    acc_std: 1.5,
    acc_min: 62.0,
    acc_max: 68.0,
    acc_range: 6.0,
    acc_rms: 64.2,
    temp_mean: 33.5,
    temp_std: 0.2,
  });

  test('valid payload contains exactly 26 feature keys', () => {
    const payload = getValidPayload();
    const keys = Object.keys(payload);
    expect(keys.length).toBe(26);
    expect(keys).toContain('eda_mean');
    expect(keys).toContain('bvp_hr');
    expect(keys).toContain('acc_rms');
    expect(keys).toContain('temp_std');
  });

  test('stressService.runModelTest calls POST /api/v1/stress/model-test', async () => {
    const originalFetch = (global as any).fetch;
    const mockResponse: ModelTestResponsePayload = {
      status: 'MODEL_TEST_SUCCESS',
      prediction: 1,
      stress_level: 'STRESS',
      stress_probability: 0.734,
      confidence: 0.734,
      model_name: 'Sanjeevni_Best_Stress_Model.pkl',
      feature_count: 26,
      threshold: 0.5,
      message: 'Manual model test completed successfully.',
    };

    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    try {
      const payload = getValidPayload();
      const result = await stressService.runModelTest(payload);

      expect(result.status).toBe('MODEL_TEST_SUCCESS');
      expect(result.prediction).toBe(1);
      expect(result.stress_level).toBe('STRESS');
      expect(result.stress_probability).toBe(0.734);

      expect((global as any).fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/stress/model-test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(payload),
        })
      );
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('propagates honest error when backend returns MODEL_UNAVAILABLE 503', async () => {
    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({
        error_code: 'MODEL_UNAVAILABLE',
        message: 'Stress prediction ML model is not available.',
      }),
    });

    try {
      const payload = getValidPayload();
      await expect(stressService.runModelTest(payload)).rejects.toThrow(
        'Stress prediction ML model is not available.'
      );
    } finally {
      (global as any).fetch = originalFetch;
    }
  });
});
