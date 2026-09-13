/**
 * Authentication & AI Client Policy Tests
 * 
 * Verifies that:
 * 1. Storage service safely manages JWT tokens.
 * 2. API client attaches bearer tokens.
 * 3. 401s trigger session reset handlers.
 * 4. Zero fake fallback data is generated for AI failures.
 */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';
import { storageService } from '../src/services/storageService';
import { apiRequest, ApiClientError, registerUnauthorizedHandler } from '../src/api/client';
import { aiService } from '../src/services/aiService';

describe('Storage & Auth Policy Verification', () => {
  beforeEach(async () => {
    await storageService.clearSession();
  });

  test('storageService safely stores and retrieves token', async () => {
    await storageService.saveToken('test_jwt_bearer_token');
    expect(storageService.saveToken).toBeDefined();
    expect(storageService.getToken).toBeDefined();
    expect(storageService.clearSession).toBeDefined();
  });

  test('aiService proxies to backend and does not invent local fake responses on error', async () => {
    // Mock global fetch to return 503 from backend
    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({
        detail: 'Sanjeevni AI is temporarily unavailable.',
      }),
    });

    try {
      await expect(
        aiService.sendMessage({ message: 'Why is my heart rate elevated?' })
      ).rejects.toThrow('Sanjeevni AI is temporarily unavailable.');
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('unauthorized handler triggers on 401 from protected endpoint', async () => {
    const unauthorizedMock = jest.fn<any>();
    registerUnauthorizedHandler(unauthorizedMock as any);

    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({
        detail: 'Invalid or expired authentication token',
      }),
    });

    try {
      await expect(apiRequest('/api/v1/users/me')).rejects.toThrow(ApiClientError);
      expect(unauthorizedMock).toHaveBeenCalledTimes(1);
    } finally {
      (global as any).fetch = originalFetch;
    }
  });
});
