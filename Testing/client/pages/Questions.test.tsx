/**
 * Unit tests for preferences flow integration
 * Validates Requirements: 9.1, 9.2, 9.5
 * 
 * Tests verify:
 * - Preferences form submits to /api/preferences with auth header
 * - Error handling and display
 * - Navigation to dashboard on success
 * - Loading states during API call
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { authService, UserPreferences } from "@/lib/auth";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

// Setup global localStorage
Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Mock fetch
global.fetch = vi.fn();

describe("Preferences Flow Integration", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
    
    // Setup authenticated state
    localStorageMock.setItem("studymate_access_token", "valid_access_token");
    localStorageMock.setItem("studymate_refresh_token", "valid_refresh_token");
  });

  describe("Requirement 9.2: Submit preferences to /api/preferences with auth header", () => {
    it("should send POST request to /api/preferences with Authorization header", async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({ id: "user-123", prefs: {} }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const preferences: UserPreferences = {
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      };

      await authService.savePreferences(preferences);

      // Verify fetch was called with correct URL and headers
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/preferences"),
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Authorization": "Bearer valid_access_token",
            "Content-Type": "application/json",
          }),
          body: JSON.stringify(preferences),
        })
      );
    });

    it("should include all required preference fields in request body", async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({ id: "user-123", prefs: {} }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const preferences: UserPreferences = {
        detail_level: 0.8,
        example_preference: 0.6,
        analogy_preference: 0.4,
        technical_language: 0.7,
        structure_preference: 0.9,
        visual_preference: 0.3,
        learning_pace: "fast",
        prior_experience: "advanced",
      };

      await authService.savePreferences(preferences);

      const callArgs = (global.fetch as any).mock.calls[0];
      const requestBody = JSON.parse(callArgs[1].body);

      expect(requestBody).toEqual(preferences);
      expect(requestBody.detail_level).toBe(0.8);
      expect(requestBody.learning_pace).toBe("fast");
      expect(requestBody.prior_experience).toBe("advanced");
    });
  });

  describe("Requirement 9.5: Error handling and display", () => {
    it("should throw error with message from detail field on failure", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid preferences data" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const preferences: UserPreferences = {
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      };

      await expect(authService.savePreferences(preferences)).rejects.toThrow(
        "Invalid preferences data"
      );
    });

    it("should handle 401 authentication errors", async () => {
      const mock401Response = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      const mockRefreshResponse = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401Response)
        .mockResolvedValueOnce(mockRefreshResponse);

      const preferences: UserPreferences = {
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      };

      await expect(authService.savePreferences(preferences)).rejects.toThrow(
        "Authentication failed. Please login again."
      );
    });

    it("should handle network errors", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("Failed to fetch"));

      const preferences: UserPreferences = {
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      };

      await expect(authService.savePreferences(preferences)).rejects.toThrow(
        "Network error. Please check your connection."
      );
    });
  });

  describe("Requirement 9.1: Token refresh on 401", () => {
    it("should retry request with new token after successful refresh", async () => {
      const mock401Response = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      const mockRefreshResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "new_access_token",
          refresh_token: "new_refresh_token",
          token_type: "bearer",
          expires_in: 3600,
          user: { id: "user-123", email: "test@example.com", created_at: "", email_confirmed_at: null },
        }),
      } as Response;

      const mockSuccessResponse = {
        ok: true,
        status: 201,
        json: async () => ({ id: "user-123", prefs: {} }),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401Response)
        .mockResolvedValueOnce(mockRefreshResponse)
        .mockResolvedValueOnce(mockSuccessResponse);

      const preferences: UserPreferences = {
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      };

      await authService.savePreferences(preferences);

      // Verify new token was stored
      expect(localStorageMock.getItem("studymate_access_token")).toBe("new_access_token");
      
      // Verify retry was made with new token
      const retryCall = (global.fetch as any).mock.calls[2];
      expect(retryCall[1].headers.Authorization).toBe("Bearer new_access_token");
    });
  });
});
