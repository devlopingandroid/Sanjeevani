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
    const isDev = typeof __DEV__ !== 'undefined' ? __DEV__ : process.env.NODE_ENV !== 'production';

    // 1. Sanitize & Normalize local file URI for React Native FormData
    let cleanUri = (fileUri || '').trim();
    if (Platform.OS === 'android') {
      if (!cleanUri.startsWith('file://') && !cleanUri.startsWith('content://')) {
        if (cleanUri.startsWith('file:/')) {
          cleanUri = cleanUri.replace(/^file:\/*/, 'file:///');
        } else {
          cleanUri = `file://${cleanUri}`;
        }
      }
    }

    // 2. Resolve MIME type safely from parameter or file extension
    let derivedMime = mimeType ? mimeType.trim().toLowerCase() : '';
    if (!derivedMime || derivedMime === 'image' || !derivedMime.includes('/')) {
      const lower = cleanUri.toLowerCase();
      if (lower.endsWith('.png')) derivedMime = 'image/png';
      else if (lower.endsWith('.webp')) derivedMime = 'image/webp';
      else if (lower.endsWith('.gif')) derivedMime = 'image/gif';
      else if (lower.endsWith('.heic')) derivedMime = 'image/heic';
      else if (lower.endsWith('.heif')) derivedMime = 'image/heif';
      else derivedMime = 'image/jpeg';
    }
    if (derivedMime === 'image/jpg') derivedMime = 'image/jpeg';

    // 3. Resolve Filename safely
    let derivedName = fileName ? fileName.trim() : '';
    if (!derivedName) {
      const extensionMap: Record<string, string> = {
        'image/png': 'png',
        'image/webp': 'webp',
        'image/gif': 'gif',
        'image/heic': 'heic',
        'image/heif': 'heif',
        'image/jpeg': 'jpg',
      };
      const ext = extensionMap[derivedMime] || 'jpg';
      derivedName = `avatar_${Date.now()}.${ext}`;
    }

    // 4. Temporary safe debug logging (never log JWT/secrets)
    if (isDev) {
      console.log(`[Avatar] Selected URI: ${cleanUri}`);
      console.log(`[Avatar] MIME type: ${derivedMime}`);
      console.log(`[Avatar] Filename: ${derivedName}`);
      console.log(`[Avatar] Uploading multipart avatar`);
    }

    // 5. React Native / Expo compatible multipart FormData object
    const formData = new FormData();
    formData.append('file', {
      uri: cleanUri,
      name: derivedName,
      type: derivedMime,
    } as any);

    const result = await apiRequest<UserProfile>(ENDPOINTS.USERS.AVATAR, {
      method: 'POST',
      body: formData,
    });

    if (isDev) {
      console.log(`[Avatar] Upload successful`);
    }

    return result;
  },

  async forgotPassword(email: string): Promise<AuthStatusResponse> {
    return await apiRequest<AuthStatusResponse>(ENDPOINTS.AUTH.FORGOT_PASSWORD, {
      method: 'POST',
      body: JSON.stringify({ email: email.trim().toLowerCase() }),
    });
  },
};

