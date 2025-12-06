import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatInput from './ChatInput';

describe('ChatInput Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays permission denied error with retry button', async () => {
    // Mock getUserMedia to reject with permission error
    const mockGetUserMedia = vi.fn().mockRejectedValue(
      Object.assign(new Error('Permission denied'), { name: 'NotAllowedError' })
    );
    
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      configurable: true,
    });

    // Mock MediaRecorder
    global.MediaRecorder = vi.fn() as any;

    const { container } = render(<ChatInput />);
    
    // Find and click microphone button
    const micButton = container.querySelector('button[aria-label="Record voice message"]');
    expect(micButton).toBeTruthy();
    
    if (micButton) {
      fireEvent.click(micButton);
    }

    // Wait for error to appear - use getAllByText and check the visible one in the alert
    await waitFor(() => {
      const alert = screen.getByRole('alert');
      expect(alert).toBeTruthy();
      const errorTexts = screen.getAllByText(/Microphone permission denied/i);
      expect(errorTexts.length).toBeGreaterThan(0);
    });

    // Check for retry button
    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeTruthy();

    // Check for dismiss button
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    expect(dismissButton).toBeTruthy();
  });

  it('displays file too large error with retry button', async () => {
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });
    
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      configurable: true,
    });

    // Mock MediaRecorder with large file
    const mockMediaRecorder = {
      start: vi.fn(),
      stop: vi.fn(),
      state: 'inactive',
      ondataavailable: null as any,
      onstop: null as any,
      onerror: null as any,
      mimeType: 'audio/webm',
    };

    global.MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder) as any;
    (global.MediaRecorder as any).isTypeSupported = vi.fn().mockReturnValue(true);

    global.AudioContext = vi.fn().mockImplementation(() => ({
      createMediaStreamSource: vi.fn().mockReturnValue({
        connect: vi.fn(),
      }),
      createAnalyser: vi.fn().mockReturnValue({
        fftSize: 256,
        smoothingTimeConstant: 0.8,
      }),
      close: vi.fn(),
    })) as any;

    const { container } = render(<ChatInput />);
    
    // Find and click microphone button
    const micButton = container.querySelector('button[aria-label="Record voice message"]');
    if (micButton) {
      fireEvent.click(micButton);
    }

    await waitFor(() => {
      expect(mockMediaRecorder.start).toHaveBeenCalled();
    });

    // Simulate recording stop with large file (>25MB)
    const largeBlob = new Blob(['x'.repeat(26 * 1024 * 1024)], { type: 'audio/webm' });
    if (mockMediaRecorder.onstop) {
      // Simulate chunks being collected
      if (mockMediaRecorder.ondataavailable) {
        mockMediaRecorder.ondataavailable({ data: largeBlob } as any);
      }
      mockMediaRecorder.onstop();
    }

    // Wait for error to appear
    await waitFor(() => {
      const errorText = screen.getByText(/File Too Large/i);
      expect(errorText).toBeTruthy();
    });

    // Check for retry button
    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeTruthy();
  });

  it('displays transcription service unavailable error with retry button', async () => {
    const mockGetUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });
    
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      configurable: true,
    });

    // Mock fetch to return 503 service unavailable
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ success: false, error: 'AI Brain service is unavailable' }),
    });

    // Mock MediaRecorder
    const mockMediaRecorder = {
      start: vi.fn(),
      stop: vi.fn(),
      state: 'inactive',
      ondataavailable: null as any,
      onstop: null as any,
      onerror: null as any,
      mimeType: 'audio/webm',
    };

    global.MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder) as any;
    (global.MediaRecorder as any).isTypeSupported = vi.fn().mockReturnValue(true);

    global.AudioContext = vi.fn().mockImplementation(() => ({
      createMediaStreamSource: vi.fn().mockReturnValue({
        connect: vi.fn(),
      }),
      createAnalyser: vi.fn().mockReturnValue({
        fftSize: 256,
        smoothingTimeConstant: 0.8,
      }),
      close: vi.fn(),
    })) as any;

    const { container } = render(<ChatInput />);
    
    // Find and click microphone button
    const micButton = container.querySelector('button[aria-label="Record voice message"]');
    if (micButton) {
      fireEvent.click(micButton);
    }

    await waitFor(() => {
      expect(mockMediaRecorder.start).toHaveBeenCalled();
    });

    // Simulate recording stop with valid small file
    const smallBlob = new Blob(['test audio data'], { type: 'audio/webm' });
    if (mockMediaRecorder.ondataavailable) {
      mockMediaRecorder.ondataavailable({ data: smallBlob } as any);
    }
    if (mockMediaRecorder.onstop) {
      mockMediaRecorder.onstop();
    }

    // Wait for transcription error to appear
    await waitFor(() => {
      const errorText = screen.getByText(/Service Unavailable/i);
      expect(errorText).toBeTruthy();
    }, { timeout: 3000 });

    // Check for retry button
    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeTruthy();
  });

  it('dismisses error when dismiss button is clicked', async () => {
    const mockGetUserMedia = vi.fn().mockRejectedValue(
      Object.assign(new Error('Permission denied'), { name: 'NotAllowedError' })
    );
    
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      configurable: true,
    });

    global.MediaRecorder = vi.fn() as any;

    const { container } = render(<ChatInput />);
    
    // Trigger error
    const micButton = container.querySelector('button[aria-label="Record voice message"]');
    if (micButton) {
      fireEvent.click(micButton);
    }

    // Wait for error to appear
    await waitFor(() => {
      const alert = screen.getByRole('alert');
      expect(alert).toBeTruthy();
    });

    // Click dismiss button
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);

    // Error alert should be gone
    await waitFor(() => {
      const alert = screen.queryByRole('alert');
      expect(alert).toBeNull();
    });
  });
});
