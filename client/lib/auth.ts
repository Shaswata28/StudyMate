/**
 * Authentication Service
 * 
 * Handles all authentication operations including:
 * - User registration (signup)
 * - User login
 * - Token management (access & refresh tokens)
 * - Session management
 * - Logout
 * - Authenticated API requests
 */

// API base URL - adjust based on environment
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'studymate_access_token';
const REFRESH_TOKEN_KEY = 'studymate_refresh_token';
const USER_KEY = 'studymate_user';

// Types
export interface User {
  id: string;
  email: string;
  created_at: string;
  email_confirmed_at: string | null;
  last_sign_in_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: User;
}

export interface SignupData {
  email: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AcademicProfile {
  grade: string[];
  semester_type: 'double' | 'tri';
  semester: number;
  subject: string[];
}

export interface UserPreferences {
  detail_level: number; // 0-1 scale
  example_preference: number; // 0-1 scale
  analogy_preference: number; // 0-1 scale
  technical_language: number; // 0-1 scale
  structure_preference: number; // 0-1 scale
  visual_preference: number; // 0-1 scale
  learning_pace: 'slow' | 'moderate' | 'fast';
  prior_experience: 'beginner' | 'intermediate' | 'advanced' | 'expert';
}

/**
 * Authentication Service Class
 */
class AuthService {
  /**
   * Register a new user
   */
  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const authData: AuthResponse = await response.json();
    this.setTokens(authData);
    return authData;
  }

  /**
   * Login an existing user
   */
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const authData: AuthResponse = await response.json();
    this.setTokens(authData);
    return authData;
  }

  /**
   * Logout the current user
   */
  async logout(): Promise<void> {
    const token = this.getAccessToken();
    
    if (token) {
      try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout request failed:', error);
        // Continue with local logout even if API call fails
      }
    }

    this.clearTokens();
  }

  /**
   * Get current session information
   */
  async getSession(): Promise<{ user: User; session: any } | null> {
    const token = this.getAccessToken();
    
    if (!token) {
      return null;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/session`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          const refreshed = await this.refreshToken();
          if (refreshed) {
            return this.getSession(); // Retry with new token
          }
        }
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Get session failed:', error);
      return null;
    }
  }

  /**
   * Refresh the access token using refresh token
   */
  async refreshToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return false;
      }

      const authData: AuthResponse = await response.json();
      this.setTokens(authData);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearTokens();
      return false;
    }
  }

  /**
   * Make an authenticated API request
   * Automatically handles token refresh on 401 errors
   */
  async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getAccessToken();
    
    if (!token) {
      throw new Error('No access token available');
    }

    // Add authorization header
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    };

    let response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle token expiration
    if (response.status === 401) {
      const refreshed = await this.refreshToken();
      
      if (refreshed) {
        // Retry request with new token
        const newToken = this.getAccessToken();
        headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(url, {
          ...options,
          headers,
        });
      } else {
        throw new Error('Authentication failed. Please login again.');
      }
    }

    return response;
  }

  /**
   * Save academic profile (Step 2 of signup)
   */
  async saveAcademicProfile(profile: AcademicProfile): Promise<void> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/academic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save academic profile');
    }
  }

  /**
   * Save user preferences (from questionnaire)
   */
  async savePreferences(preferences: UserPreferences): Promise<void> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prefs: preferences }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save preferences');
    }
  }

  /**
   * Get user preferences
   */
  async getPreferences(): Promise<UserPreferences | null> {
    try {
      const response = await this.fetchWithAuth(`${API_BASE_URL}/preferences`);

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data.prefs;
    } catch (error) {
      console.error('Get preferences failed:', error);
      return null;
    }
  }

  /**
   * Get academic profile
   */
  async getAcademicProfile(): Promise<AcademicProfile | null> {
    try {
      const response = await this.fetchWithAuth(`${API_BASE_URL}/academic`);

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Get academic profile failed:', error);
      return null;
    }
  }

  // Token management methods

  private setTokens(authData: AuthResponse): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, authData.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, authData.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user));
  }

  private clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export helper functions
export const isAuthenticated = () => authService.isAuthenticated();
export const getCurrentUser = () => authService.getCurrentUser();
export const logout = () => authService.logout();
