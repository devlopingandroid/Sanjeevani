/**
 * Authentication Service
 * 
 * Interacts with FastAPI /api/v1/auth and /api/v1/users endpoints.
 * Never invents mock users or fake tokens.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import {
  AuthTokenResponse,
  UserProfile,
  AuthStatusResponse,
} from '../api/types';

import { Platform } from 'react-native';

export const authService = {
  async register(fullName: string, email: string, password: string): Promise<UserProfile> {
    return await apiRequest<UserProfile>(ENDPOINTS.AUTH.REGISTER, {
      method: 'POST',
      body: JSON.stringify({
        full_name: fullName,
        email: email.trim().toLowerCase(),
        password,
      }),
    });
  },

  async login(email: string, password: string): Promise<AuthTokenResponse> {
    return await apiRequest<AuthTokenResponse>(ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: JSON.stringify({
        email: email.trim().toLowerCase(),
        password,
      }),
    });
  },

  async getMe(): Promise<UserProfile> {
    return await apiRequest<UserProfile>(ENDPOINTS.USERS.ME, {
      method: 'GET',
    });
  },

  async refreshToken(): Promise<AuthTokenResponse> {
    return await apiRequest<AuthTokenResponse>(ENDPOINTS.AUTH.REFRESH, {
      method: 'POST',
    });
  },

  async logout(): Promise<AuthStatusResponse> {
    try {
      return await apiRequest<AuthStatusResponse>(ENDPOINTS.AUTH.LOGOUT, {
        method: 'POST',
      });
    } catch {
      return { success: true, message: 'Client session cleared' };
    }
  },

  async updateProfile(updates: { full_name?: string; profile_image_url?: string }): Promise<UserProfile> {
    return await apiRequest<UserProfile>(ENDPOINTS.USERS.ME, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async uploadAvatar(fileUri: string, mimeType?: string, fileName?: string): Promise<UserProfile> {
    const formData = new FormData();
    let type = mimeType || 'image/jpeg';
    if (!mimeType) {
      const lower = fileUri.toLowerCase();
      if (lower.endsWith('.png')) type = 'image/png';
      else if (lower.endsWith('.webp')) type = 'image/webp';
      else if (lower.endsWith('.gif')) type = 'image/gif';
      else if (lower.endsWith('.heic')) type = 'image/heic';
      else type = 'image/jpeg';
    }
    if (type === 'image/jpg') type = 'image/jpeg';

    const ext = type.includes('png') ? 'png' : type.includes('webp') ? 'webp' : type.includes('gif') ? 'gif' : 'jpg';
    const name = fileName || `avatar_${Date.now()}.${ext}`;

    const formattedUri = Platform.OS === 'android' && !fileUri.startsWith('file://') && !fileUri.startsWith('content://')
      ? `file://${fileUri}`
      : fileUri;

    formData.append('file', {
      uri: formattedUri,
      type,
      name,
    } as any);

    return await apiRequest<UserProfile>(ENDPOINTS.USERS.AVATAR, {
      method: 'POST',
      body: formData,
    });
  },

  async forgotPassword(email: string): Promise<AuthStatusResponse> {
    return await apiRequest<AuthStatusResponse>(ENDPOINTS.AUTH.FORGOT_PASSWORD, {
      method: 'POST',
      body: JSON.stringify({ email: email.trim().toLowerCase() }),
    });
  },
};

