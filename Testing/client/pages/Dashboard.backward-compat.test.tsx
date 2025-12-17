import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
    // Simple transformation for testing
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
    // Simple transformation for testing
    return materials.map((m: any) => ({
      id: m.id,
      name: m.name,
      type: m.file_type,
    }));
  }),
}));

describe('Dashboard Backward Compatibility', () => {
  let mockFetch: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock fetch for chat API
    mockFetch = vi.fn();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should load existing chat history and display messages', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock existing chat history
    (apiService.getChatHistory as any).mockResolvedValue([
      {
        id: 'history-1',
        course_id: 'course-1',
        history: [
          { role: 'user', content: 'Hello from history' },
          { role: 'model', content: 'Hi there from history!' },
        ],
        created_at: '2024-01-01T00:00:00Z',
      },
    ]);

    // Mock materials (empty for this test)
    (apiService.getMaterials as any).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for courses and chat history to load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
      expect(apiService.getChatHistory).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
    });

    // Verify loaded messages appear
    await waitFor(() => {
      expect(screen.getByText('Hello from history')).toBeTruthy();
      expect(screen.getByText('Hi there from history!')).toBeTruthy();
    });
  });

  it('should load existing materials and display them', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock existing materials
    (apiService.getMaterials as any).mockResolvedValue([
      {
        id: 'material-1',
        name: 'existing-file.pdf',
        file_type: 'application/pdf',
        processing_status: 'completed',
      },
      {
        id: 'material-2',
        name: 'another-file.docx',
        file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        processing_status: 'completed',
      },
    ]);

    // Mock chat history (empty for this test)
    (apiService.getChatHistory as any).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for courses and materials to load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
      expect(apiService.getMaterials).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
    });

    // Verify materials count badge appears (materials are loaded)
    await waitFor(() => {
      const materialsButton = screen.getByLabelText('View materials');
      expect(materialsButton).toBeTruthy();
      // The badge should show "2" for 2 materials
      const badge = materialsButton.querySelector('span');
      expect(badge?.textContent).toBe('2');
    });
  });

  it('should work with empty loaded history', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock empty chat history
    (apiService.getChatHistory as any).mockResolvedValue([]);

    // Mock materials (empty for this test)
    (apiService.getMaterials as any).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for courses to load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
      expect(apiService.getChatHistory).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
    });

    // Verify the Workspace component is rendered (functionality works with empty history)
    await waitFor(() => {
      const materialsButton = screen.getByLabelText('View materials');
      expect(materialsButton).toBeTruthy();
    });

    // Verify that getChatHistory was called, meaning the system attempted to load history
    expect(apiService.getChatHistory).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
  });

  it('should work with empty loaded materials', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Test Course' },
    ]);

    // Mock empty materials
    (apiService.getMaterials as any).mockResolvedValue([]);

    // Mock chat history (empty for this test)
    (apiService.getChatHistory as any).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for courses to load
    await waitFor(() => {
      expect(courseService.getCourses).toHaveBeenCalled();
      expect(apiService.getMaterials).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
    });

    // Verify materials button is available (functionality works with empty materials)
    await waitFor(() => {
      const materialsButton = screen.getByLabelText('View materials');
      expect(materialsButton).toBeTruthy();
      // No badge should appear when there are no materials
      const badge = materialsButton.querySelector('span');
      expect(badge).toBeNull();
    });
  });

  it('should clear previous data when switching courses', async () => {
    const { courseService } = await import('@/lib/courses');
    const { apiService } = await import('@/lib/api');

    // Mock multiple courses
    (courseService.getCourses as any).mockResolvedValue([
      { id: 'course-1', name: 'Course 1' },
      { id: 'course-2', name: 'Course 2' },
    ]);

    // Mock chat history for both courses
    (apiService.getChatHistory as any).mockImplementation((courseId: string) => {
      if (courseId === 'course-1') {
        return Promise.resolve([
          {
            id: 'history-1',
            course_id: 'course-1',
            history: [{ role: 'user', content: 'Course 1 message' }],
            created_at: '2024-01-01T00:00:00Z',
          },
        ]);
      } else if (courseId === 'course-2') {
        return Promise.resolve([
          {
            id: 'history-2',
            course_id: 'course-2',
            history: [{ role: 'user', content: 'Course 2 message' }],
            created_at: '2024-01-02T00:00:00Z',
          },
        ]);
      }
      return Promise.resolve([]);
    });

    // Mock materials for both courses
    (apiService.getMaterials as any).mockImplementation((courseId: string) => {
      if (courseId === 'course-1') {
        return Promise.resolve([
          { id: 'mat-1', name: 'course1-file.pdf', file_type: 'application/pdf' },
        ]);
      } else if (courseId === 'course-2') {
        return Promise.resolve([
          { id: 'mat-2', name: 'course2-file.pdf', file_type: 'application/pdf' },
          { id: 'mat-3', name: 'course2-file2.pdf', file_type: 'application/pdf' },
        ]);
      }
      return Promise.resolve([]);
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for initial course (Course 1) to load
    await waitFor(() => {
      expect(screen.getByText('Course 1 message')).toBeTruthy();
    });

    // Verify Course 1 materials badge shows "1"
    await waitFor(() => {
      const materialsButton = screen.getByLabelText('View materials');
      const badge = materialsButton.querySelector('span');
      expect(badge?.textContent).toBe('1');
    });

    // Verify getChatHistory and getMaterials were called for course-1
    expect(apiService.getChatHistory).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));
    expect(apiService.getMaterials).toHaveBeenCalledWith('course-1', expect.any(AbortSignal));

    // Clear the mock call history
    vi.clearAllMocks();

    // Find and click on Course 2 button
    const course2Button = screen.getByLabelText('Select course Course 2');
    course2Button.click();

    // Wait for Course 2 data to load
    await waitFor(() => {
      expect(screen.getByText('Course 2 message')).toBeTruthy();
    });

    // Verify Course 2 materials badge shows "2"
    await waitFor(() => {
      const materialsButton = screen.getByLabelText('View materials');
      const badge = materialsButton.querySelector('span');
      expect(badge?.textContent).toBe('2');
    });

    // Verify getChatHistory and getMaterials were called for course-2
    expect(apiService.getChatHistory).toHaveBeenCalledWith('course-2', expect.any(AbortSignal));
    expect(apiService.getMaterials).toHaveBeenCalledWith('course-2', expect.any(AbortSignal));

    // Verify Course 1 message is no longer visible
    expect(screen.queryByText('Course 1 message')).toBeNull();
  });
});
