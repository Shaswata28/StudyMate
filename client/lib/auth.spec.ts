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

describe("AuthService - Error Handling", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorageMock.clear();
    // Clear all mocks
    vi.clearAllMocks();
  });

  describe("Error message extraction from detail field", () => {
    it("should extract error message from detail field (string)", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "A user with this email already exists" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("A user with this email already exists");
    });

    it("should extract error message from detail field (object)", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: { message: "Custom error message" } }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.login({ email: "test@example.com", password: "wrong" })
      ).rejects.toThrow("Custom error message");
    });

    it("should fallback to message field if detail is not present", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ message: "Fallback error message" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Fallback error message");
    });

    it("should use status-based error message when JSON parsing fails", async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        headers: new Headers({ "content-type": "text/html" }),
        json: async () => {
          throw new Error("Not JSON");
        },
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.login({ email: "test@example.com", password: "wrong" })
      ).rejects.toThrow("Invalid or expired authentication token");
    });
  });

  describe("Token storage after successful signup", () => {
    it("should store tokens in localStorage after successful signup", async () => {
      const mockAuthResponse = {
        access_token: "mock_access_token",
        refresh_token: "mock_refresh_token",
        token_type: "bearer",
        expires_in: 3600,
        user: {
          id: "user-123",
          email: "test@example.com",
          created_at: "2024-01-01T00:00:00Z",
          email_confirmed_at: null,
        },
      };

      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => mockAuthResponse,
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.signup({ email: "test@example.com", password: "password123" });

      expect(localStorageMock.getItem("studymate_access_token")).toBe("mock_access_token");
      expect(localStorageMock.getItem("studymate_refresh_token")).toBe("mock_refresh_token");
      expect(localStorageMock.getItem("studymate_user")).toBe(JSON.stringify(mockAuthResponse.user));
    });
  });

  describe("Token refresh on 401 errors", () => {
    it("should attempt token refresh on 401 error", async () => {
      // Setup: Store initial tokens
      localStorageMock.setItem("studymate_access_token", "expired_token");
      localStorageMock.setItem("studymate_refresh_token", "valid_refresh_token");

      // First call returns 401
      const mock401Response = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      // Refresh token call succeeds
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

      // Retry with new token succeeds
      const mockSuccessResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        }),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401Response) // First call fails with 401
        .mockResolvedValueOnce(mockRefreshResponse) // Refresh succeeds
        .mockResolvedValueOnce(mockSuccessResponse); // Retry succeeds

      const profile = {
        grade: ["10"],
        semester_type: "double" as const,
        semester: 1,
        subject: ["Math"],
      };

      await authService.saveAcademicProfile(profile);

      // Verify new token was stored
      expect(localStorageMock.getItem("studymate_access_token")).toBe("new_access_token");
      expect(localStorageMock.getItem("studymate_refresh_token")).toBe("new_refresh_token");
    });

    it("should clear tokens when refresh fails", async () => {
      // Setup: Store initial tokens
      localStorageMock.setItem("studymate_access_token", "expired_token");
      localStorageMock.setItem("studymate_refresh_token", "invalid_refresh_token");

      // First call returns 401
      const mock401Response = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      // Refresh token call fails
      const mockRefreshFailResponse = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401Response) // First call fails with 401
        .mockResolvedValueOnce(mockRefreshFailResponse); // Refresh fails

      const profile = {
        grade: ["10"],
        semester_type: "double" as const,
        semester: 1,
        subject: ["Math"],
      };

      await expect(authService.saveAcademicProfile(profile)).rejects.toThrow(
        "Authentication failed. Please login again."
      );

      // Verify tokens were cleared
      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();
      expect(localStorageMock.getItem("studymate_refresh_token")).toBeNull();
      expect(localStorageMock.getItem("studymate_user")).toBeNull();
    });
  });

  describe("Token clearing on logout", () => {
    it("should clear tokens on logout", async () => {
      // Setup: Store tokens
      localStorageMock.setItem("studymate_access_token", "access_token");
      localStorageMock.setItem("studymate_refresh_token", "refresh_token");
      localStorageMock.setItem("studymate_user", JSON.stringify({ id: "user-123" }));

      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ message: "Logged out successfully" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.logout();

      // Verify tokens were cleared
      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();
      expect(localStorageMock.getItem("studymate_refresh_token")).toBeNull();
      expect(localStorageMock.getItem("studymate_user")).toBeNull();
    });

    it("should clear tokens even if logout API call fails", async () => {
      // Setup: Store tokens
      localStorageMock.setItem("studymate_access_token", "access_token");
      localStorageMock.setItem("studymate_refresh_token", "refresh_token");

      (global.fetch as any).mockRejectedValueOnce(new Error("Network error"));

      await authService.logout();

      // Verify tokens were cleared despite error
      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();
      expect(localStorageMock.getItem("studymate_refresh_token")).toBeNull();
    });
  });

  describe("Network error handling", () => {
    it("should handle network errors gracefully", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("Failed to fetch"));

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Network error. Please check your connection.");
    });
  });

  describe("API Base URL Configuration", () => {
    it("should use configured API base URL for all requests", async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        json: async () => ({
          access_token: "token",
          refresh_token: "refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: { id: "1", email: "test@example.com", created_at: "2024-01-01T00:00:00Z", email_confirmed_at: null },
        }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await authService.signup({ email: "test@example.com", password: "password123" });

      // Verify fetch was called with the correct URL
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/auth\/signup$/),
        expect.any(Object)
      );
    });

    it("should use configured API base URL for authenticated requests", async () => {
      localStorageMock.setItem("studymate_access_token", "valid_token");

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

      // Verify fetch was called with the correct URL
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/academic$/),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer valid_token",
          }),
        })
      );
    });
  });

  describe("Comprehensive Error Handling - HTTP Status Codes", () => {
    it("should handle 400 validation errors correctly", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Password must be at least 8 characters" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "short" })
      ).rejects.toThrow("Password must be at least 8 characters");
    });

    it("should handle 401 authentication errors correctly", async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid credentials" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.login({ email: "test@example.com", password: "wrong" })
      ).rejects.toThrow("Invalid credentials");
    });

    it("should handle 403 forbidden errors correctly", async () => {
      const mockResponse = {
        ok: false,
        status: 403,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "You do not have permission" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("You do not have permission");
    });

    it("should handle 404 not found errors correctly", async () => {
      localStorageMock.setItem("studymate_access_token", "valid_token");

      const mockResponse = {
        ok: false,
        status: 404,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Resource not found" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.getAcademicProfile()
      ).resolves.toBeNull();
    });

    it("should handle 409 conflict errors correctly", async () => {
      const mockResponse = {
        ok: false,
        status: 409,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "A user with this email already exists" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "existing@example.com", password: "password123" })
      ).rejects.toThrow("A user with this email already exists");
    });

    it("should handle 500 server errors correctly", async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Internal server error" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Internal server error");
    });

    it("should use default error message for 500 when detail is missing", async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("An unexpected error occurred. Please try again.");
    });
  });

  describe("Comprehensive Error Handling - Network Errors", () => {
    it("should handle network timeout errors", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("Network timeout"));

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Network timeout");
    });

    it("should handle DNS resolution failures", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("getaddrinfo ENOTFOUND"));

      await expect(
        authService.login({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("getaddrinfo ENOTFOUND");
    });

    it("should handle connection refused errors", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("ECONNREFUSED"));

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("ECONNREFUSED");
    });

    it("should handle fetch failures with generic network error", async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error("Failed to fetch"));

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Network error. Please check your connection.");
    });

    it("should handle network errors in authenticated requests", async () => {
      localStorageMock.setItem("studymate_access_token", "valid_token");

      (global.fetch as any).mockRejectedValueOnce(new Error("Network error"));

      await expect(
        authService.saveAcademicProfile({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow("Network error");
    });
  });

  describe("Comprehensive Error Handling - Validation Errors", () => {
    it("should handle missing required fields error", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Email is required" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "", password: "password123" })
      ).rejects.toThrow("Email is required");
    });

    it("should handle invalid email format error", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid email format" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "invalid-email", password: "password123" })
      ).rejects.toThrow("Invalid email format");
    });

    it("should handle password too short error", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Password must be at least 8 characters" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "short" })
      ).rejects.toThrow("Password must be at least 8 characters");
    });

    it("should handle academic profile validation errors", async () => {
      localStorageMock.setItem("studymate_access_token", "valid_token");

      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Grade is required" }),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.saveAcademicProfile({
          grade: [],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow("Grade is required");
    });
  });

  describe("Comprehensive Error Handling - Authentication Flow", () => {
    it("should handle expired token with successful refresh", async () => {
      localStorageMock.setItem("studymate_access_token", "expired_token");
      localStorageMock.setItem("studymate_refresh_token", "valid_refresh");

      const mock401 = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      const mockRefresh = {
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "new_token",
          refresh_token: "new_refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: { id: "1", email: "test@example.com", created_at: "2024-01-01T00:00:00Z", email_confirmed_at: null },
        }),
      } as Response;

      const mockSuccess = {
        ok: true,
        status: 200,
        json: async () => ({ grade: ["10"], semester_type: "double", semester: 1, subject: ["Math"] }),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401)
        .mockResolvedValueOnce(mockRefresh)
        .mockResolvedValueOnce(mockSuccess);

      const result = await authService.getAcademicProfile();
      expect(result).toBeTruthy();
      expect(localStorageMock.getItem("studymate_access_token")).toBe("new_token");
    });

    it("should handle expired token with failed refresh", async () => {
      localStorageMock.setItem("studymate_access_token", "expired_token");
      localStorageMock.setItem("studymate_refresh_token", "invalid_refresh");

      const mock401 = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      const mockRefreshFail = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      (global.fetch as any)
        .mockResolvedValueOnce(mock401)
        .mockResolvedValueOnce(mockRefreshFail);

      await expect(
        authService.saveAcademicProfile({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow("Authentication failed. Please login again.");

      expect(localStorageMock.getItem("studymate_access_token")).toBeNull();
    });

    it("should handle multiple 401 errors without infinite loop", async () => {
      localStorageMock.setItem("studymate_access_token", "expired_token");
      localStorageMock.setItem("studymate_refresh_token", "valid_refresh");

      const mock401 = {
        ok: false,
        status: 401,
        headers: new Headers(),
      } as Response;

      const mockRefresh = {
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "new_token",
          refresh_token: "new_refresh",
          token_type: "bearer",
          expires_in: 3600,
          user: { id: "1", email: "test@example.com", created_at: "2024-01-01T00:00:00Z", email_confirmed_at: null },
        }),
      } as Response;

      // Second request also returns 401 (shouldn't trigger another refresh)
      (global.fetch as any)
        .mockResolvedValueOnce(mock401)
        .mockResolvedValueOnce(mockRefresh)
        .mockResolvedValueOnce(mock401);

      await expect(
        authService.saveAcademicProfile({
          grade: ["10"],
          semester_type: "double",
          semester: 1,
          subject: ["Math"],
        })
      ).rejects.toThrow();
    });
  });

  describe("Comprehensive Error Handling - Content-Type Handling", () => {
    it("should handle non-JSON error responses", async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        headers: new Headers({ "content-type": "text/html" }),
        json: async () => {
          throw new Error("Not JSON");
        },
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("An unexpected error occurred. Please try again.");
    });

    it("should handle empty response body", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({}),
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Invalid request. Please check your input.");
    });

    it("should handle malformed JSON in error response", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => {
          throw new Error("Unexpected token");
        },
      } as Response;

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      await expect(
        authService.signup({ email: "test@example.com", password: "password123" })
      ).rejects.toThrow("Invalid request. Please check your input.");
    });
  });
});
