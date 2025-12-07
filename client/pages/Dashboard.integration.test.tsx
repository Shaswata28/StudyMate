import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';

// Mock scrollIntoView for jsdom
Element.prototype.scrollIntoView = vi.fn();

// Mock dependencies
vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    user: { id: 'test-user-id', email: 'test@example.com' },
    isAuthenticated: true,
  }),
}));

vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('@/lib/auth', () => ({
  authService: {
    getAccessToken: () => 'mock-token',
    logout: vi.fn(),
    fetchWithAuth: async (url: string, options?: any) => {
      return global.fetch(url, {
        ...options,
        headers: {
          ...options?.headers,
          'Authorization': 'Bearer mock-token',
        },
      });
    },
  },
}));

vi.mock('@/lib/courses', () => ({
  courseService: {
    getCourses: vi.fn(),
    createCourse: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => ({
  apiService: {
    getChatHistory: vi.fn(),
    getMaterials: vi.fn(),
  },
  transformChatHistory: vi.fn((records) => {
    return records.flatMap((record: any) => 
      record.history.map((msg: any, idx: number) => ({
        id: `${record.id}-${idx}`,
        text: msg.content,
        isAI: msg.role === 'model',
        timestamp: new Date(record.created_at),
      }))
    );
  }),
  transformMaterials: vi.fn((materials) => {
    return materials.map((m: any) => ({
      id: m.id,
      name: m.name,
      type: m.file_type,
    }));
  }),
}));

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should complete full flow: refresh → courses load → select course → data loads', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Math 101' },
      { id: 'course-2', name: 'Physics 201' },
    ]);

    // Mock chat history for course-1
    (apiService.getChatHistory as any).mockImplementation((courseId: string) => {
      if (courseId === 'course-1') {
        return Promise.resolve([
          {
            id: 'history-1',
            course_id: 'course-1',
            history: [
              { role: 'user', content: 'What is calculus?' },
              { role: 'model', content: 'Calculus is the study of change...' },
            ],
            created_at: '2024-01-01T10:00:00Z',
          },
        ]);
      }
      return Promise.resolve([]);
    });

    // Mock materials for course-1
    (apiService.getMaterials as any).mockImplementation((courseId: string) => {
      if (courseId === 'course-1') {
        return Promise.resolve([
          {
            id: 'mat-1',
            name: 'calculus-notes.pdf',
            file_type: 'application/pdf',
            processing_status: 'completed',
          },
        ]);
      }
      return Promise.resolve([]);
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Step 1: Verify courses load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
    });

    // Step 2: Verify first course is selected automatically
    await waitFor(() => {
      expect(apiService.getChatHistory).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
      expect(apiService.getMaterials).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
    });

    // Step 3: Verify chat history loads and displays
    await waitFor(() => {
      expect(screen.getByText('What is calculus?')).toBeTruthy();
      expect(screen.getByText('Calculus is the study of change...')).toBeTruthy();
    });

    // Step 4: Verify materials load
    await waitFor(() => {
      const materialsButton = screen.getByLabelText('View materials');
      const badge = materialsButton.querySelector('span');
      expect(badge?.textContent).toBe('1');
    });
  });

  it('should handle concurrent operations: send message while loading history', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock slow chat history loading
    (apiService.getChatHistory as any).mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve([
            {
              id: 'history-1',
              course_id: 'course-1',
              history: [{ role: 'user', content: 'Old message' }],
              created_at: '2024-01-01T10:00:00Z',
            },
          ]);
        }, 100);
      });
    });

    // Mock materials
    (apiService.getMaterials as any).mockResolvedValue([]);

    // Mock chat API
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ response: 'AI response' }),
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for courses to load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
    });

    // Find input and send button
    const input = screen.getByPlaceholderText('Ask anything');
    const sendButton = screen.getByLabelText('Send message');

    // Send a message while history is still loading
    fireEvent.change(input, { target: { value: 'New message' } });
    fireEvent.click(sendButton);

    // Verify new message appears
    await waitFor(() => {
      expect(screen.getByText('New message')).toBeTruthy();
    });

    // Wait for history to finish loading
    await waitFor(() => {
      expect(screen.getByText('Old message')).toBeTruthy();
    });

    // Verify both messages are present
    expect(screen.getByText('New message')).toBeTruthy();
    expect(screen.getByText('Old message')).toBeTruthy();
  });

  it('should handle error scenarios with proper recovery', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');
    const { toast } = await import('@/lib/toast');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock chat history failure
    (apiService.getChatHistory as any).mockRejectedValueOnce(
      new Error('Network error. Please check your connection.')
    );

    // Mock materials success
    (apiService.getMaterials as any).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for error to occur
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('Network error')
      );
    });

    // Verify materials still loaded (error isolation)
    expect(apiService.getMaterials).toHaveBeenCalled();

    // Mock successful retry
    (apiService.getChatHistory as any).mockResolvedValueOnce([
      {
        id: 'history-1',
        course_id: 'course-1',
        history: [{ role: 'user', content: 'Recovered message' }],
        created_at: '2024-01-01T10:00:00Z',
      },
    ]);

    // Find and click retry button
    const retryButton = screen.getByText(/retry/i);
    fireEvent.click(retryButton);

    // Verify message appears after retry
    await waitFor(() => {
      expect(screen.getByText('Recovered message')).toBeTruthy();
    });
  });

  it('should verify no console errors during normal operation', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Spy on console.error
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock chat history
    (apiService.getChatHistory as any).mockResolvedValue([]);

    // Mock materials
    (apiService.getMaterials as any).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for everything to load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
      expect(apiService.getChatHistory).toHaveBeenCalled();
      expect(apiService.getMaterials).toHaveBeenCalled();
    });

    // Verify no console errors (except React Router warnings which are expected)
    const errorCalls = consoleErrorSpy.mock.calls.filter(
      (call) => !call[0]?.includes?.('React Router Future Flag Warning')
    );
    expect(errorCalls.length).toBe(0);

    consoleErrorSpy.mockRestore();
  });
});
