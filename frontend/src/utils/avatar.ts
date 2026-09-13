/**
 * Avatar & Profile Utilities
 */
import { getApiBaseUrl } from '../api/client';

export function resolveAvatarUrl(url?: string | null): string | null {
  if (!url || typeof url !== 'string' || url.trim().length === 0) {
    return null;
  }
  const trimmed = url.trim();
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('file://')) {
    return trimmed;
  }
  const baseUrl = getApiBaseUrl();
  return `${baseUrl}${trimmed.startsWith('/') ? '' : '/'}${trimmed}`;
}

export function getUserInitials(fullName?: string | null, email?: string | null): string {
  if (fullName && fullName.trim().length > 0) {
    const parts = fullName.trim().split(/\s+/);
    if (parts.length === 1) {
      return parts[0].substring(0, 1).toUpperCase();
    }
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  if (email && email.trim().length > 0) {
    return email.trim()[0].toUpperCase();
  }
  return 'U';
}
