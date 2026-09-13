/**
 * Auth Context
 * 
 * Manages authenticated user state, JWT tokens, session persistence via SecureStore,
 * login, registration, and clean logout.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserProfile } from '../api/types';
import { authService } from '../services/authService';
import { storageService } from '../services/storageService';
import { registerUnauthorizedHandler } from '../api/client';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
  updateUser: (updatedUser: UserProfile) => Promise<void>;
  refreshUser: () => Promise<UserProfile>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(async () => {
    try {
      if (token) {
        await authService.logout();
      }
    } catch {
      // Ignore network errors during logout
    } finally {
      await storageService.clearSession();
      setUser(null);
      setToken(null);
    }
  }, [token]);

  // Register global 401 handler
  useEffect(() => {
    registerUnauthorizedHandler(() => {
      logout();
    });
  }, [logout]);

  const restoreSession = useCallback(async () => {
    try {
      setIsLoading(true);
      const savedToken = await storageService.getToken();
      if (!savedToken) {
        setUser(null);
        setToken(null);
        return;
      }

      setToken(savedToken);

      // Validate token with backend /users/me
      try {
        const currentUser = await authService.getMe();
        setUser(currentUser);
        await storageService.saveUser(currentUser);
      } catch (err: any) {
        if (err?.statusCode === 401) {
          // Token expired or invalid
          await storageService.clearSession();
          setUser(null);
          setToken(null);
        } else {
          // Offline or network error: attempt to load cached user
          const cachedUser = await storageService.getUser<UserProfile>();
          if (cachedUser) {
            setUser(cachedUser);
          }
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const login = async (email: string, password: string) => {
    const authResp = await authService.login(email, password);
    await storageService.saveToken(authResp.access_token);
    setToken(authResp.access_token);

    // Fetch verified profile from backend
    const profile = await authService.getMe();
    await storageService.saveUser(profile);
    setUser(profile);
  };

  const register = async (fullName: string, email: string, password: string) => {
    await authService.register(fullName, email, password);
    // Automatically log in after registration
    await login(email, password);
  };

  const updateUser = async (updatedUser: UserProfile) => {
    setUser(updatedUser);
    await storageService.saveUser(updatedUser);
  };

  const refreshUser = async (): Promise<UserProfile> => {
    const profile = await authService.getMe();
    setUser(profile);
    await storageService.saveUser(profile);
    return profile;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
        restoreSession,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
