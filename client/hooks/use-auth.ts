/**
 * useAuth Hook
 * 
 * React hook for authentication state management
 * Provides easy access to auth functions and user state
 */

import { useState, useEffect, useCallback } from 'react';
import { authService, User, SignupData, LoginData, AcademicProfile, UserPreferences } from '@/lib/auth';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      const currentUser = authService.getCurrentUser();
      
      if (currentUser) {
        // Verify session is still valid
        const session = await authService.getSession();
        if (session) {
          setUser(session.user);
          setIsAuthenticated(true);
        } else {
          // Session invalid, clear tokens
          authService.logout();
          setUser(null);
          setIsAuthenticated(false);
        }
      }
      
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Signup function
  const signup = useCallback(async (data: SignupData) => {
    setIsLoading(true);
    try {
      const response = await authService.signup(data);
      setUser(response.user);
      setIsAuthenticated(true);
      return response;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Login function
  const login = useCallback(async (data: LoginData) => {
    setIsLoading(true);
    try {
      const response = await authService.login(data);
      setUser(response.user);
      setIsAuthenticated(true);
      return response;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save academic profile
  const saveAcademicProfile = useCallback(async (profile: AcademicProfile) => {
    return authService.saveAcademicProfile(profile);
  }, []);

  // Save preferences
  const savePreferences = useCallback(async (preferences: UserPreferences) => {
    return authService.savePreferences(preferences);
  }, []);

  // Get preferences
  const getPreferences = useCallback(async () => {
    return authService.getPreferences();
  }, []);

  // Get academic profile
  const getAcademicProfile = useCallback(async () => {
    return authService.getAcademicProfile();
  }, []);

  return {
    user,
    isLoading,
    isAuthenticated,
    signup,
    login,
    logout,
    saveAcademicProfile,
    savePreferences,
    getPreferences,
    getAcademicProfile,
  };
}
