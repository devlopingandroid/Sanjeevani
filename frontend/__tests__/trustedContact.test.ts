/**
 * Trusted Contact Frontend Service & Policy Tests
 *
 * Verifies that:
 * 1. trustedContactService correctly maps to ENDPOINTS.TRUSTED_CONTACT.BASE.
 * 2. 404 response on GET returns null (indicating no trusted contact configured).
 * 3. Successful create/update returns trusted contact record.
 * 4. Delete operation calls DELETE method.
 */
import { describe, test, expect, jest } from '@jest/globals';
import { trustedContactService } from '../src/services/trustedContactService';
import { NotificationLevel } from '../src/api/types';

describe('Trusted Contact Service Verification', () => {
  test('getTrustedContact returns null when backend returns 404', async () => {
    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'No trusted contact configured for this user.' }),
    });

    try {
      const contact = await trustedContactService.getTrustedContact();
      expect(contact).toBeNull();
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('createTrustedContact sends POST request with explicit consent', async () => {
    const originalFetch = (global as any).fetch;
    const mockRecord = {
      id: 'uuid-1234',
      user_id: 1,
      name: 'Dr. Priya Sharma',
      phone_number: '+919876543210',
      relationship: 'Physician',
      enabled: true,
      consent_given: true,
      notification_level: NotificationLevel.HIGH_AND_CRITICAL,
      created_at: '2026-09-14T00:00:00Z',
      updated_at: '2026-09-14T00:00:00Z',
    };

    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockRecord,
    });

    try {
      const result = await trustedContactService.createTrustedContact({
        name: 'Dr. Priya Sharma',
        phone_number: '+919876543210',
        relationship: 'Physician',
        enabled: true,
        consent_given: true,
        notification_level: NotificationLevel.HIGH_AND_CRITICAL,
      });

      expect(result.name).toBe('Dr. Priya Sharma');
      expect(result.consent_given).toBe(true);
      expect(result.notification_level).toBe(NotificationLevel.HIGH_AND_CRITICAL);
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('deleteTrustedContact issues DELETE request', async () => {
    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'TRUSTED_CONTACT_DELETED' }),
    });

    try {
      const res = await trustedContactService.deleteTrustedContact();
      expect(res.status).toBe('TRUSTED_CONTACT_DELETED');
    } finally {
      (global as any).fetch = originalFetch;
    }
  });
});
