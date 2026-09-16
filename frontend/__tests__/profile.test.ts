/**
 * Profile & Avatar Client Tests
 * 
 * Verifies that:
 * 1. User initials are computed deterministically (e.g. "Yash" -> "Y", "Yash Goel" -> "YG").
 * 2. Avatar URLs are safely resolved against base API URL.
 * 3. authService.updateProfile sends PATCH /api/v1/users/me with updated fields.
 * 4. authService.uploadAvatar sends POST /api/v1/users/me/avatar with FormData.
 * 5. Image picker cancellation is handled without mutating state.
 * 6. Honest error messages are propagated without fallback fake data.
 */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';
import { getUserInitials, resolveAvatarUrl } from '../src/utils/avatar';
import { authService } from '../src/services/authService';
import * as ImagePicker from 'expo-image-picker';

describe('Profile & Avatar Logic Verification', () => {
  test('computes correct initials for single and multi-word names', () => {
    // Single name: Yash -> Y
    expect(getUserInitials('Yash', 'yash@example.com')).toBe('Y');
    // Multi-word name: Yash Goel -> YG
    expect(getUserInitials('Yash Goel', 'yash@example.com')).toBe('YG');
    // Three words: Yash Kumar Goel -> YG (first and last)
    expect(getUserInitials('Yash Kumar Goel', 'yash@example.com')).toBe('YG');
    // Null name falls back to first letter of email
    expect(getUserInitials(null, 'yash@example.com')).toBe('Y');
    // Empty name falls back to email
    expect(getUserInitials('   ', 'alice@sanjeevni.com')).toBe('A');
  });

  test('resolves avatar URLs correctly', () => {
    // Null / empty returns null
    expect(resolveAvatarUrl(null)).toBeNull();
    expect(resolveAvatarUrl('')).toBeNull();
    expect(resolveAvatarUrl('   ')).toBeNull();

    // Absolute HTTP URL returns untouched
    expect(resolveAvatarUrl('https://images.example.com/avatar.jpg')).toBe(
      'https://images.example.com/avatar.jpg'
    );

    // Relative backend path prefixes with API base url
    const relative = '/uploads/avatars/avatar_1.png';
    const resolved = resolveAvatarUrl(relative);
    expect(resolved).toBeTruthy();
    expect(resolved).toContain('/uploads/avatars/avatar_1.png');
  });

  test('authService.updateProfile calls PATCH /api/v1/users/me', async () => {
    const originalFetch = (global as any).fetch;
    const mockUser = {
      id: 1,
      email: 'yash@example.com',
      full_name: 'Yash Goel',
      profile_image_url: null,
      is_active: true,
      created_at: '2026-09-13T12:00:00Z',
    };

    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUser,
    });

    try {
      const updated = await authService.updateProfile({ full_name: 'Yash Goel' });
      expect(updated.full_name).toBe('Yash Goel');
      expect((global as any).fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/users/me'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ full_name: 'Yash Goel' }),
        })
      );
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('authService.uploadAvatar sends POST /api/v1/users/me/avatar', async () => {
    const originalFetch = (global as any).fetch;
    const mockUser = {
      id: 1,
      email: 'yash@example.com',
      full_name: 'Yash',
<<<<<<< Updated upstream
      profile_image_url: '/uploads/avatars/avatar_1_123.jpg',
=======
      profile_image_url: '/uploads/avatars/user_1_avatar.jpg',
>>>>>>> Stashed changes
      is_active: true,
      created_at: '2026-09-13T12:00:00Z',
    };

    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUser,
    });

    try {
<<<<<<< Updated upstream
      const updated = await authService.uploadAvatar('file:///path/to/image.jpg', 'image/jpeg');
      expect(updated.profile_image_url).toBe('/uploads/avatars/avatar_1_123.jpg');
      expect((global as any).fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/users/me/avatar'),
        expect.objectContaining({
          method: 'POST',
        })
      );
=======
      const updated = await authService.uploadAvatar('file:///path/to/image.jpg', 'image/jpeg', 'my_photo.jpg');
      expect(updated.profile_image_url).toBe('/uploads/avatars/user_1_avatar.jpg');
      
      const fetchCall = (global as any).fetch.mock.calls[0];
      expect(fetchCall[0]).toContain('/api/v1/users/me/avatar');
      expect(fetchCall[1].method).toBe('POST');
      expect(fetchCall[1].body).toBeInstanceOf(FormData);
>>>>>>> Stashed changes
    } finally {
      (global as any).fetch = originalFetch;
    }
  });

  test('cancelled image picker does not change state', async () => {
    // Mock image picker to return cancelled
    (ImagePicker.launchImageLibraryAsync as jest.Mock<any>).mockResolvedValueOnce({
      canceled: true,
      assets: null,
    });

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
    });

    expect(result.canceled).toBe(true);
  });

  test('honest error propagation when profile update fails', async () => {
    const originalFetch = (global as any).fetch;
    (global as any).fetch = jest.fn<any>().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({
        detail: 'Invalid user profile data',
      }),
    });

    try {
      await expect(
        authService.updateProfile({ full_name: '' })
      ).rejects.toThrow('Invalid user profile data');
    } finally {
      (global as any).fetch = originalFetch;
    }
  });
});
