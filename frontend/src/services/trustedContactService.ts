/**
 * Trusted Contact Service (Frontend)
 *
 * Provides API wrappers for managing user's trusted contact settings.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import {
  TrustedContactRecord,
  TrustedContactCreatePayload,
  TrustedContactUpdatePayload,
} from '../api/types';

export const trustedContactService = {
  async getTrustedContact(): Promise<TrustedContactRecord | null> {
    try {
      return await apiRequest<TrustedContactRecord>(
        ENDPOINTS.TRUSTED_CONTACT.BASE,
        { method: 'GET' }
      );
    } catch (err: any) {
      if (err?.statusCode === 404 || err?.status === 404 || err?.message?.includes('404')) {
        return null;
      }
      throw err;
    }
  },

  async createTrustedContact(
    payload: TrustedContactCreatePayload
  ): Promise<TrustedContactRecord> {
    return await apiRequest<TrustedContactRecord>(
      ENDPOINTS.TRUSTED_CONTACT.BASE,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  async updateTrustedContact(
    payload: TrustedContactUpdatePayload
  ): Promise<TrustedContactRecord> {
    return await apiRequest<TrustedContactRecord>(
      ENDPOINTS.TRUSTED_CONTACT.BASE,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  },

  async deleteTrustedContact(): Promise<{ status: string }> {
    return await apiRequest<{ status: string }>(
      ENDPOINTS.TRUSTED_CONTACT.BASE,
      { method: 'DELETE' }
    );
  },
};
