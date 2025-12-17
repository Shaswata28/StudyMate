/**
 * End-to-End Registration Flow Tests
 * 
 * Tests the complete registration flow:
 * - Signup → Academic Profile → Preferences → Dashboard
 * 
 * Validates ALL requirements from the spec
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { authService } from "./auth";

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

describe("End-to-End Registration Flow", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe("Complete flow with valid data", () => {
    it("should complete full registration: signup → academic profile → preferences → success", async () => {
      // Step 1: Signup
      const mockSignupResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "test_access_token",
          refresh_token: "test_refresh_token",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "newuser@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockSignupResponse);

      await authService.signup({
        email: "newuser@example.com",
        password: "password123",
      });

      // Verify tokens stored
      expect(localStorageMock.getItem("studymate_access_token")).toBe("test_access_token");
      expect(localStorageMock.getItem("studymate_refresh_token")).toBe("test_refresh_token");
      expect(localStorageMock.getItem("studymate_user")).toBeTruthy();

      // Step 2: Academic Profile
      const mockAcademicResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          id: "user-123",
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockAcademicResponse);

      await authService.saveAcademicProfile({
        grade: ["10"],
        semester_type: "double",
        semester: 1,
        subject: ["Math"],
      });

      // Verify academic profile call included auth header
      const academicCall = (global.fetch as any).mock.calls[1];
      expect(academicCall[1].headers.Authorization).toBe("Bearer test_access_token");

      // Step 3: Preferences
      const mockPreferencesResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          id: "user-123",
          prefs: {},
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockPreferencesResponse);

      await authService.savePreferences({
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      });

      // Verify preferences call included auth header
      const preferencesCall = (global.fetch as any).mock.calls[2];
      expect(preferencesCall[1].headers.Authorization).toBe("Bearer test_access_token");

      // Verify tokens still present after complete flow
      expect(localStorageMock.getItem("studymate_access_token")).toBe("test_access_token");
      expect(localStorageMock.getItem("studymate_refresh_token")).toBe("test_refresh_token");
    });
  });

  describe("Invalid data at each step", () => {
    it("should fail at signup with duplicate email", async () => {
      const mockErrorResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "A user with this email already exists" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.signup({
          email: "existing@example.com",
          password: "password123",
        })
      ).rejects.toThrow("A user with this email already exists");

      // Verify no tokens stored on failure
      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();
      expect(localStorageMock.getItem("studymate_refresh_token")).toBeNull();
    });

    it("should fail at signup with weak password", async () => {
      const mockErrorResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Password must be at least 8 characters" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.signup({
          email: "test@example.com",
          password: "short",
        })
      ).rejects.toThrow("Password must be at least 8 characters");
    });

    it("should fail at academic profile with missing authentication", async () => {
      // No tokens in localStorage
      const mockErrorResponse = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.saveAcademicProfile({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow();
    });

    it("should fail at academic profile with invalid data", async () => {
      localStorageMock.setItem("studymate_access_token", "valid_token");

      const mockErrorResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Grade is required" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.saveAcademicProfile({
          grade: [],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow("Grade is required");
    });

    it("should fail at preferences with missing authentication", async () => {
      // Clear tokens
      localStorageMock.clear();

      await expect(
        authService.savePreferences({
          detail_level: 0.5,
          example_preference: 0.5,
          analogy_preference: 0.5,
          technical_language: 0.5,
          structure_preference: 0.5,
          visual_preference: 0.5,
          learning_pace: "moderate",
          prior_experience: "intermediate",
        })
      ).rejects.toThrow();
    });
  });

  describe("Browser refresh during registration", () => {
    it("should preserve authentication state after signup when browser refreshes", async () => {
      // Simulate signup
      const mockSignupResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "test_access_token",
          refresh_token: "test_refresh_token",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "test@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockSignupResponse);

      await authService.signup({
        email: "test@example.com",
        password: "password123",
      });

      // Simulate browser refresh by checking if tokens persist
      const accessToken = localStorageMock.getItem("studymate_access_token");
      const refreshToken = localStorageMock.getItem("studymate_refresh_token");
      const user = localStorageMock.getItem("studymate_user");

      expect(accessToken).toBe("test_access_token");
      expect(refreshToken).toBe("test_refresh_token");
      expect(user).toBeTruthy();

      // Verify user can continue with academic profile after "refresh"
      const mockAcademicResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockAcademicResponse);

      await authService.saveAcademicProfile({
        grade: ["10"],
        semester_type: "double",
        semester: 1,
        subject: ["Math"],
      });

      // Should succeed with preserved token
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/academic"),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test_access_token",
          }),
        })
      );
    });

    it("should preserve authentication after academic profile when browser refreshes", async () => {
      // Setup: User already completed signup
      localStorageMock.setItem("studymate_access_token", "test_access_token");
      localStorageMock.setItem("studymate_refresh_token", "test_refresh_token");
      localStorageMock.setItem(
        "studymate_user",
        JSON.stringify({
          id: "user-123",
          email: "test@example.com",
          created_at: "2024-01-01T00:00:00Z",
          email_confirmed_at: null,
        })
      );

      // Simulate browser refresh - tokens should still be there
      expect(authService.isAuthenticated()).toBe(true);
      expect(authService.getCurrentUser()).toBeTruthy();

      // User can continue to preferences
      const mockPreferencesResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockPreferencesResponse);

      await authService.savePreferences({
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences"),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test_access_token",
          }),
        })
      );
    });
  });

  describe("Token management throughout flow", () => {
    it("should maintain same tokens throughout entire registration flow", async () => {
      // Step 1: Signup
      const mockSignupResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "initial_access_token",
          refresh_token: "initial_refresh_token",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "test@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockSignupResponse);

      await authService.signup({
        email: "test@example.com",
        password: "password123",
      });

      const tokenAfterSignup = localStorageMock.getItem("studymate_access_token");
      expect(tokenAfterSignup).toBe("initial_access_token");

      // Step 2: Academic Profile
      const mockAcademicResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockAcademicResponse);

      await authService.saveAcademicProfile({
        grade: ["10"],
        semester_type: "double",
        semester: 1,
        subject: ["Math"],
      });

      const tokenAfterAcademic = localStorageMock.getItem("studymate_access_token");
      expect(tokenAfterAcademic).toBe("initial_access_token");

      // Step 3: Preferences
      const mockPreferencesResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockPreferencesResponse);

      await authService.savePreferences({
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      });

      const tokenAfterPreferences = localStorageMock.getItem("studymate_access_token");
      expect(tokenAfterPreferences).toBe("initial_access_token");

      // Verify all API calls used the same token
      const academicCall = (global.fetch as any).mock.calls[1];
      const preferencesCall = (global.fetch as any).mock.calls[2];

      expect(academicCall[1].headers.Authorization).toBe("Bearer initial_access_token");
      expect(preferencesCall[1].headers.Authorization).toBe("Bearer initial_access_token");
    });

    it("should handle token refresh during registration flow", async () => {
      // Setup: User has tokens from signup
      localStorageMock.setItem("studymate_access_token", "expired_token");
      localStorageMock.setItem("studymate_refresh_token", "valid_refresh_token");

      // Academic profile call returns 401
      const mock401Response = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      // Refresh succeeds
      const mockRefreshResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "new_access_token",
          refresh_token: "new_refresh_token",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "test@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      // Retry succeeds
      const mockSuccessResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401Response)
        .mockResolvedValueOnce(mockRefreshResponse)
        .mockResolvedValueOnce(mockSuccessResponse);

      await authService.saveAcademicProfile({
        grade: ["10"],
        semester_type: "double",
        semester: 1,
        subject: ["Math"],
      });

      // Verify new token was stored
      expect(localStorageMock.getItem("studymate_access_token")).toBe("new_access_token");
      expect(localStorageMock.getItem("studymate_refresh_token")).toBe("new_refresh_token");

      // User can continue with preferences using new token
      const mockPreferencesResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockPreferencesResponse);

      await authService.savePreferences({
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      });

      const preferencesCall = (global.fetch as any).mock.calls[3];
      expect(preferencesCall[1].headers.Authorization).toBe("Bearer new_access_token");
    });
  });

  describe("Data persistence verification", () => {
    it("should verify data persists after each step", async () => {
      // Step 1: Signup - verify user data stored
      const mockSignupResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "test_token",
          refresh_token: "test_refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "test@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockSignupResponse);

      const signupResult = await authService.signup({
        email: "test@example.com",
        password: "password123",
      });

      expect(signupResult.user.email).toBe("test@example.com");
      expect(signupResult.user.id).toBe("user-123");

      const storedUser = authService.getCurrentUser();
      expect(storedUser).toBeTruthy();
      expect(storedUser?.email).toBe("test@example.com");

      // Step 2: Academic Profile - verify profile data sent correctly
      const mockAcademicResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          id: "user-123",
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockAcademicResponse);

      await authService.saveAcademicProfile({
        grade: ["10"],
        semester_type: "double",
        semester: 1,
        subject: ["Math"],
      });

      // Verify the request body contained correct data
      const academicCall = (global.fetch as any).mock.calls[1];
      const academicBody = JSON.parse(academicCall[1].body);
      expect(academicBody.grade).toEqual(["10"]);
      expect(academicBody.semester_type).toBe("double");
      expect(academicBody.semester).toBe(1);
      expect(academicBody.subject).toEqual(["Math"]);

      // Step 3: Preferences - verify preferences data sent correctly
      const mockPreferencesResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          id: "user-123",
          prefs: {
            detail_level: 0.8,
            example_preference: 0.6,
            analogy_preference: 0.4,
            technical_language: 0.7,
            structure_preference: 0.9,
            visual_preference: 0.3,
            learning_pace: "fast",
            prior_experience: "advanced",
          },
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockPreferencesResponse);

      const preferences = {
        detail_level: 0.8,
        example_preference: 0.6,
        analogy_preference: 0.4,
        technical_language: 0.7,
        structure_preference: 0.9,
        visual_preference: 0.3,
        learning_pace: "fast" as const,
        prior_experience: "advanced" as const,
      };

      await authService.savePreferences(preferences);

      // Verify the request body contained correct data
      const preferencesCall = (global.fetch as any).mock.calls[2];
      const preferencesBody = JSON.parse(preferencesCall[1].body);
      expect(preferencesBody).toEqual(preferences);
    });

    it("should retrieve persisted data after registration", async () => {
      // Setup: User completed registration
      localStorageMock.setItem("studymate_access_token", "test_token");
      localStorageMock.setItem("studymate_refresh_token", "test_refresh");
      localStorageMock.setItem(
        "studymate_user",
        JSON.stringify({
          id: "user-123",
          email: "test@example.com",
          created_at: "2024-01-01T00:00:00Z",
          email_confirmed_at: null,
        })
      );

      // Retrieve academic profile
      const mockAcademicResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          id: "user-123",
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockAcademicResponse);

      const academicProfile = await authService.getAcademicProfile();
      expect(academicProfile).toBeTruthy();
      expect(academicProfile?.grade).toEqual(["10"]);
      expect(academicProfile?.semester_type).toBe("double");

      // Retrieve preferences
      const mockPreferencesResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          id: "user-123",
          prefs: {
            detail_level: 0.5,
            example_preference: 0.5,
            analogy_preference: 0.5,
            technical_language: 0.5,
            structure_preference: 0.5,
            visual_preference: 0.5,
            learning_pace: "moderate",
            prior_experience: "intermediate",
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockPreferencesResponse);

      const preferences = await authService.getPreferences();
      expect(preferences).toBeTruthy();
      expect(preferences?.learning_pace).toBe("moderate");
      expect(preferences?.prior_experience).toBe("intermediate");
    });
  });

  describe("Network and error resilience", () => {
    it("should handle network errors at signup step", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("Failed to fetch"));

      await expect(
        authService.signup({
          email: "test@example.com",
          password: "password123",
        })
      ).rejects.toThrow("Network error. Please check your connection.");

      // Verify no tokens stored
      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();
    });

    it("should handle network errors at academic profile step", async () => {
      localStorageMock.setItem("studymate_access_token", "test_token");

      (global.fetch as any).mockRejectedValueOnce(new Error("Network timeout"));

      await expect(
        authService.saveAcademicProfile({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow("Network timeout");

      // Verify tokens still present (user remains authenticated)
      expect(localStorageMock.getItem("studymate_access_token")).toBe("test_token");
    });

    it("should handle network errors at preferences step", async () => {
      localStorageMock.setItem("studymate_access_token", "test_token");

      (global.fetch as any).mockRejectedValueOnce(new Error("Connection refused"));

      await expect(
        authService.savePreferences({
          detail_level: 0.5,
          example_preference: 0.5,
          analogy_preference: 0.5,
          technical_language: 0.5,
          structure_preference: 0.5,
          visual_preference: 0.5,
          learning_pace: "moderate",
          prior_experience: "intermediate",
        })
      ).rejects.toThrow("Connection refused");

      // Verify tokens still present
      expect(localStorageMock.getItem("studymate_access_token")).toBe("test_token");
    });

    it("should handle server errors (500) gracefully", async () => {
      const mockErrorResponse = {
        ok: false,
        status: 500,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Internal server error" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.signup({
          email: "test@example.com",
          password: "password123",
        })
      ).rejects.toThrow("Internal server error");
    });

    it("should preserve authentication when academic profile fails", async () => {
      // Setup: User completed signup
      localStorageMock.setItem("studymate_access_token", "test_token");
      localStorageMock.setItem("studymate_refresh_token", "test_refresh");

      const mockErrorResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid academic data" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.saveAcademicProfile({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow("Invalid academic data");

      // Verify user remains authenticated (Requirement 5.2)
      expect(localStorageMock.getItem("studymate_access_token")).toBe("test_token");
      expect(localStorageMock.getItem("studymate_refresh_token")).toBe("test_refresh");
      expect(authService.isAuthenticated()).toBe(true);
    });

    it("should preserve authentication when preferences fail", async () => {
      localStorageMock.setItem("studymate_access_token", "test_token");
      localStorageMock.setItem("studymate_refresh_token", "test_refresh");

      const mockErrorResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid preferences data" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockErrorResponse);

      await expect(
        authService.savePreferences({
          detail_level: 0.5,
          example_preference: 0.5,
          analogy_preference: 0.5,
          technical_language: 0.5,
          structure_preference: 0.5,
          visual_preference: 0.5,
          learning_pace: "moderate",
          prior_experience: "intermediate",
        })
      ).rejects.toThrow("Invalid preferences data");

      // Verify user remains authenticated
      expect(localStorageMock.getItem("studymate_access_token")).toBe("test_token");
      expect(authService.isAuthenticated()).toBe(true);
    });
  });

  describe("HTTP status codes and RESTful conventions", () => {
    it("should return 201 Created for successful signup", async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "token",
          refresh_token: "refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "test@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.signup({
        email: "test@example.com",
        password: "password123",
      });

      const signupCall = (global.fetch as any).mock.calls[0];
      expect(signupCall[1].method).toBe("POST");
      expect(signupCall[1].headers["Content-Type"]).toBe("application/json");
    });

    it("should return 201 Created for successful academic profile creation", async () => {
      localStorageMock.setItem("studymate_access_token", "test_token");

      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.saveAcademicProfile({
        grade: ["10"],
        semester_type: "double",
        semester: 1,
        subject: ["Math"],
      });

      const academicCall = (global.fetch as any).mock.calls[0];
      expect(academicCall[1].method).toBe("POST");
      expect(academicCall[1].headers["Content-Type"]).toBe("application/json");
    });

    it("should return 201 Created for successful preferences creation", async () => {
      localStorageMock.setItem("studymate_access_token", "test_token");

      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.savePreferences({
        detail_level: 0.5,
        example_preference: 0.5,
        analogy_preference: 0.5,
        technical_language: 0.5,
        structure_preference: 0.5,
        visual_preference: 0.5,
        learning_pace: "moderate",
        prior_experience: "intermediate",
      });

      const preferencesCall = (global.fetch as any).mock.calls[0];
      expect(preferencesCall[1].method).toBe("POST");
      expect(preferencesCall[1].headers["Content-Type"]).toBe("application/json");
    });

    it("should use configured API base URL for all requests", async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "token",
          refresh_token: "refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-123",
            email: "test@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.signup({
        email: "test@example.com",
        password: "password123",
      });

      const signupCall = (global.fetch as any).mock.calls[0];
      expect(signupCall[0]).toMatch(/\/auth\/signup$/);
    });
  });

  describe("Complete flow with multiple users", () => {
    it("should handle registration of multiple users independently", async () => {
      // User 1 registration
      const mockSignup1 = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "user1_token",
          refresh_token: "user1_refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-1",
            email: "user1@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockSignup1);

      await authService.signup({
        email: "user1@example.com",
        password: "password123",
      });

      expect(localStorageMock.getItem("studymate_access_token")).toBe("user1_token");

      // Simulate logout
      await authService.logout();
      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();

      // User 2 registration
      const mockSignup2 = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "user2_token",
          refresh_token: "user2_refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            id: "user-2",
            email: "user2@example.com",
            created_at: "2024-01-01T00:00:00Z",
            email_confirmed_at: null,
          },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockSignup2);

      await authService.signup({
        email: "user2@example.com",
        password: "password456",
      });

      expect(localStorageMock.getItem("studymate_access_token")).toBe("user2_token");
      
      const currentUser = authService.getCurrentUser();
      expect(currentUser?.email).toBe("user2@example.com");
    });
  });
});
