import { Plus, Send, Loader, Mic, Square, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import VoiceVisualizer from "./VoiceVisualizer";

interface ChatInputProps {
  onSend?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  isLoading?: boolean;
}

interface VoiceRecordingState {
  isRecording: boolean;
  isPaused: boolean;
  isTranscribing: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  error: string | null;
  errorType: 'permission' | 'recording' | 'transcription' | 'service' | 'filesize' | null;
  canRetry: boolean;
  mediaRecorder: MediaRecorder | null;
  audioChunks: Blob[];
  audioAnalyzer: AnalyserNode | null;
}

export default function ChatInput({ onSend, onFileUpload, isLoading = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Voice recording state
  const [voiceState, setVoiceState] = useState<VoiceRecordingState>({
    isRecording: false,
    isPaused: false,
    isTranscribing: false,
    recordingTime: 0,
    audioBlob: null,
    error: null,
    errorType: null,
    canRetry: false,
    mediaRecorder: null,
    audioChunks: [],
    audioAnalyzer: null,
  });

  // Refs for voice recording
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Check if MediaRecorder API is supported
  const isVoiceInputSupported = (): boolean => {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      typeof MediaRecorder !== "undefined"
    );
  };

  // Detect supported audio format for the browser
  const getSupportedAudioFormat = (): string => {
    const formats = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/mpeg',
    ];

    for (const format of formats) {
      if (MediaRecorder.isTypeSupported(format)) {
        return format;
      }
    }

    // Fallback to default
    return 'audio/webm';
  };

  // Get file extension from MIME type
  const getFileExtension = (mimeType: string): string => {
    if (mimeType.includes('webm')) return 'webm';
    if (mimeType.includes('ogg')) return 'ogg';
    if (mimeType.includes('mp4')) return 'mp4';
    if (mimeType.includes('mpeg')) return 'mp3';
    return 'webm'; // default
  };

  // Validate audio file size (max 25MB as per Whisper requirements)
  const validateAudioSize = (blob: Blob): { valid: boolean; error?: string } => {
    const maxSize = 25 * 1024 * 1024; // 25MB in bytes
    
    if (blob.size > maxSize) {
      const sizeMB = (blob.size / (1024 * 1024)).toFixed(2);
      return {
        valid: false,
        error: `Audio file is too large (${sizeMB}MB). Maximum size is 25MB. Please record a shorter message.`,
      };
    }
    
    return { valid: true };
  };

  // Start recording audio
  const startRecording = async () => {
    if (!isVoiceInputSupported()) {
      setVoiceState((prev) => ({
        ...prev,
        error: "Voice input is not supported in your browser",
        errorType: 'recording',
        canRetry: false,
      }));
      return;
    }

    try {
      // Request microphone permissions
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;

      // Set up AudioContext and AnalyserNode for visualizer
      // Support both standard and webkit-prefixed AudioContext for Safari compatibility
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass();
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      
      // Configure analyser for smooth visualization
      analyser.fftSize = 256; // Smaller FFT for faster processing
      analyser.smoothingTimeConstant = 0.8; // Smooth out amplitude changes
      
      // Connect audio nodes
      source.connect(analyser);

      // Initialize MediaRecorder with the audio stream and supported format
      const supportedFormat = getSupportedAudioFormat();
      const mediaRecorder = new MediaRecorder(stream, { mimeType: supportedFormat });
      const chunks: Blob[] = [];

      // Collect audio chunks as they become available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      // Handle recording errors
      mediaRecorder.onerror = (event: any) => {
        console.error('MediaRecorder error:', event.error);
        setVoiceState((prev) => ({
          ...prev,
          isRecording: false,
          error: 'Recording failed. Please try again.',
          errorType: 'recording',
          canRetry: true,
        }));
        
        // Clean up resources
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach(track => track.stop());
          audioStreamRef.current = null;
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
      };

      // Handle recording stop - create audio blob
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: mediaRecorder.mimeType });
        
        // Validate audio file size
        const validation = validateAudioSize(audioBlob);
        
        if (!validation.valid) {
          // Display error for oversized file
          setVoiceState((prev) => ({
            ...prev,
            isRecording: false,
            error: validation.error || 'Audio file is too large',
            errorType: 'filesize',
            canRetry: true,
            audioBlob: null,
          }));
        } else {
          // File size is valid, proceed with transcription
          setVoiceState((prev) => ({
            ...prev,
            audioBlob,
            isRecording: false,
          }));
        }

        // Clean up the media stream
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach(track => track.stop());
          audioStreamRef.current = null;
        }

        // Clean up AudioContext
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
      };

      // Start recording
      mediaRecorder.start();

      // Update state to reflect recording has started
      setVoiceState((prev) => ({
        ...prev,
        isRecording: true,
        mediaRecorder,
        audioChunks: chunks,
        recordingTime: 0,
        error: null,
        errorType: null,
        canRetry: false,
        audioBlob: null,
        audioAnalyzer: analyser,
      }));
    } catch (error) {
      // Handle permission denied or other errors
      let errorMessage = "Failed to access microphone";
      let errorType: 'permission' | 'recording' = 'recording';
      let canRetry = true;
      
      if (error instanceof Error) {
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
          errorMessage = "Microphone permission denied. Please allow microphone access in your browser settings and try again.";
          errorType = 'permission';
          canRetry = true;
        } else if (error.name === "NotFoundError") {
          errorMessage = "No microphone found. Please connect a microphone and try again.";
          errorType = 'recording';
          canRetry = true;
        } else if (error.name === "NotReadableError") {
          errorMessage = "Microphone is already in use by another application. Please close other apps and try again.";
          errorType = 'recording';
          canRetry = true;
        } else {
          errorMessage = `Recording failed: ${error.message}`;
          errorType = 'recording';
          canRetry = true;
        }
      }

      setVoiceState((prev) => ({
        ...prev,
        error: errorMessage,
        errorType,
        canRetry,
      }));

      // Clean up stream if it was created
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }

      // Clean up AudioContext if it was created
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
    }
  };

  // Transcribe audio blob
  const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
    try {
      // Get the appropriate file extension based on MIME type
      const extension = getFileExtension(audioBlob.type);
      const filename = `recording.${extension}`;
      
      // Create form data with audio file
      const formData = new FormData();
      formData.append('audio', audioBlob, filename);

      // Send to transcription endpoint
      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Determine error type based on status code
        if (response.status === 503) {
          throw new Error('service:' + (errorData.error || 'AI Brain service is unavailable. Please ensure it is running and try again.'));
        } else if (response.status === 504) {
          throw new Error('transcription:' + (errorData.error || 'Transcription request timed out. Please try again.'));
        } else {
          throw new Error('transcription:' + (errorData.error || `Transcription failed: ${response.statusText}`));
        }
      }

      const data = await response.json();
      
      if (!data.success || !data.text) {
        throw new Error('transcription:' + (data.error || 'Transcription failed: No text returned'));
      }

      return data.text;
    } catch (error) {
      let errorMessage = 'Failed to transcribe audio';
      let errorType = 'transcription';
      
      if (error instanceof Error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          errorMessage = 'service:Network error. Please check your connection and try again.';
        } else if (error.message.startsWith('service:') || error.message.startsWith('transcription:')) {
          // Error already formatted with type prefix
          errorMessage = error.message;
        } else {
          errorMessage = 'transcription:' + error.message;
        }
      }
      
      throw new Error(errorMessage);
    }
  };

  // Stop recording and create audio blob
  const stopRecording = () => {
    if (voiceState.mediaRecorder && voiceState.mediaRecorder.state !== "inactive") {
      voiceState.mediaRecorder.stop();
    }
  };

  // Cancel recording and discard audio
  const cancelRecording = () => {
    // Stop the MediaRecorder if it's active
    if (voiceState.mediaRecorder && voiceState.mediaRecorder.state !== "inactive") {
      voiceState.mediaRecorder.stop();
    }

    // Stop and clean up audio stream
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }

    // Clean up AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Reset state to initial
    setVoiceState({
      isRecording: false,
      isPaused: false,
      isTranscribing: false,
      recordingTime: 0,
      audioBlob: null,
      error: null,
      errorType: null,
      canRetry: false,
      mediaRecorder: null,
      audioChunks: [],
      audioAnalyzer: null,
    });
  };

  // Retry failed operation
  const handleRetry = () => {
    if (!voiceState.canRetry) return;

    // Clear error state
    setVoiceState((prev) => ({
      ...prev,
      error: null,
      errorType: null,
      canRetry: false,
    }));

    // Retry based on error type
    if (voiceState.errorType === 'permission' || voiceState.errorType === 'recording' || voiceState.errorType === 'filesize') {
      // Retry recording
      startRecording();
    } else if (voiceState.errorType === 'transcription' || voiceState.errorType === 'service') {
      // Retry transcription with existing audio blob
      if (voiceState.audioBlob) {
        setVoiceState((prev) => ({
          ...prev,
          isTranscribing: true,
          error: null,
          errorType: null,
          canRetry: false,
        }));
        
        transcribeAudio(voiceState.audioBlob)
          .then((transcribedText) => {
            setMessage(transcribedText);
            setVoiceState({
              isRecording: false,
              isPaused: false,
              isTranscribing: false,
              recordingTime: 0,
              audioBlob: null,
              error: null,
              errorType: null,
              canRetry: false,
              mediaRecorder: null,
              audioChunks: [],
              audioAnalyzer: null,
            });
            textareaRef.current?.focus();
          })
          .catch((error) => {
            const errorMessage = error instanceof Error ? error.message : 'Transcription failed';
            const [errorType, message] = errorMessage.includes(':') 
              ? errorMessage.split(':', 2) as ['service' | 'transcription', string]
              : ['transcription' as const, errorMessage];
            
            setVoiceState((prev) => ({
              ...prev,
              isTranscribing: false,
              error: message,
              errorType,
              canRetry: true,
            }));
          });
      }
    }
  };

  // Dismiss error message
  const dismissError = () => {
    setVoiceState((prev) => ({
      ...prev,
      error: null,
      errorType: null,
      canRetry: false,
      audioBlob: null,
    }));
  };

  // Request microphone permissions and start recording
  const handleMicrophoneClick = async () => {
    await startRecording();
  };

  // Handle stop button click
  const handleStopRecording = () => {
    stopRecording();
  };

  // Handle cancel button click
  const handleCancelRecording = () => {
    cancelRecording();
  };

  // Format recording time as MM:SS
  const formatRecordingTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 100)}px`;
    }
  }, [message]);

  // Recording timer effect - increments recording time every second
  useEffect(() => {
    if (voiceState.isRecording && !voiceState.isPaused) {
      recordingTimerRef.current = setInterval(() => {
        setVoiceState((prev) => ({
          ...prev,
          recordingTime: prev.recordingTime + 1,
        }));
      }, 1000);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }

    // Cleanup on unmount
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    };
  }, [voiceState.isRecording, voiceState.isPaused]);

  // Transcription effect - triggers when audioBlob is created
  useEffect(() => {
    const performTranscription = async () => {
      if (voiceState.audioBlob && !voiceState.isTranscribing && !voiceState.error) {
        // Set transcribing state
        setVoiceState((prev) => ({
          ...prev,
          isTranscribing: true,
          error: null,
          errorType: null,
          canRetry: false,
        }));

        try {
          // Transcribe the audio
          const transcribedText = await transcribeAudio(voiceState.audioBlob);
          
          // Populate input field with transcribed text
          setMessage(transcribedText);
          
          // Reset voice state
          setVoiceState({
            isRecording: false,
            isPaused: false,
            isTranscribing: false,
            recordingTime: 0,
            audioBlob: null,
            error: null,
            errorType: null,
            canRetry: false,
            mediaRecorder: null,
            audioChunks: [],
            audioAnalyzer: null,
          });

          // Focus the textarea so user can edit - use setTimeout to ensure state is updated
          setTimeout(() => {
            textareaRef.current?.focus();
            // Move cursor to end of text
            if (textareaRef.current) {
              const length = textareaRef.current.value.length;
              textareaRef.current.setSelectionRange(length, length);
            }
          }, 0);
        } catch (error) {
          // Parse error message with type prefix
          const errorMessage = error instanceof Error ? error.message : 'transcription:Transcription failed';
          const [errorType, message] = errorMessage.includes(':') 
            ? errorMessage.split(':', 2) as ['service' | 'transcription', string]
            : ['transcription' as const, errorMessage];
          
          setVoiceState((prev) => ({
            ...prev,
            isTranscribing: false,
            error: message,
            errorType,
            canRetry: true,
            // Keep audioBlob for retry capability
          }));
        }
      }
    };

    performTranscription();
  }, [voiceState.audioBlob]);

  // Keyboard navigation effect - handle Escape key to cancel recording
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape key cancels recording
      if (e.key === 'Escape' && voiceState.isRecording) {
        e.preventDefault();
        cancelRecording();
      }
    };

    // Add event listener
    window.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [voiceState.isRecording]);

  // Cleanup effect for audio streams and MediaRecorder on unmount
  useEffect(() => {
    return () => {
      // Stop and clean up MediaRecorder
      if (voiceState.mediaRecorder && voiceState.mediaRecorder.state !== "inactive") {
        voiceState.mediaRecorder.stop();
      }
      
      // Stop and clean up audio stream
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }
      
      // Close and clean up audio context
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
    };
  }, [voiceState.mediaRecorder]);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSend?.(message);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileClick = () => {
    if (!isLoading && !isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setIsUploading(true);
      onFileUpload?.(Array.from(files));
      e.target.value = "";
      // Reset uploading state after a delay
      setTimeout(() => setIsUploading(false), 1000);
    }
  };

  // Determine text size based on message length
  const getTextSizeClass = () => {
    if (message.length > 200) return "text-base";
    if (message.length > 100) return "text-lg";
    return "text-xl";
  };

  return (
    <>
      {/* Screen reader announcements for state changes */}
      <div 
        role="status" 
        aria-live="polite" 
        aria-atomic="true" 
        className="sr-only"
      >
        {voiceState.isRecording && `Recording started. Recording time: ${formatRecordingTime(voiceState.recordingTime)}`}
        {voiceState.isTranscribing && 'Transcribing audio, please wait'}
        {voiceState.error && `Error: ${voiceState.error}`}
        {message && !voiceState.isRecording && !voiceState.isTranscribing && `Message input contains ${message.length} characters`}
      </div>

      <div className="w-full max-w-[609px] mx-auto">
        {/* Error message display with retry capability */}
        {voiceState.error && (
          <div 
            className="mb-2 px-4 py-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg"
            role="alert"
            aria-live="assertive"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <p className="text-red-700 dark:text-red-300 text-sm font-medium">
                  {voiceState.errorType === 'permission' && '🎤 Permission Denied'}
                  {voiceState.errorType === 'recording' && '⚠️ Recording Failed'}
                  {voiceState.errorType === 'transcription' && '📝 Transcription Failed'}
                  {voiceState.errorType === 'service' && '🔌 Service Unavailable'}
                  {voiceState.errorType === 'filesize' && '📦 File Too Large'}
                </p>
                <p className="text-red-600 dark:text-red-400 text-sm mt-1">
                  {voiceState.error}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {voiceState.canRetry && (
                  <button
                    onClick={handleRetry}
                    className="px-3 py-1 text-xs font-medium text-red-700 dark:text-red-300 bg-red-200 dark:bg-red-800/50 hover:bg-red-300 dark:hover:bg-red-800 rounded transition-colors"
                    aria-label="Retry operation"
                  >
                    Retry
                  </button>
                )}
                <button
                  onClick={dismissError}
                  className="p-1 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-800/50 rounded transition-colors"
                  aria-label="Dismiss error message"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div 
          className="relative flex items-end bg-studymate-gray dark:bg-slate-800 rounded-[26px] shadow-lg min-h-[52px] px-4 py-3 transition-all duration-200 border border-transparent dark:border-slate-700 hover:shadow-xl"
          role="region"
          aria-label="Chat input controls"
        >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx,.txt"
          onChange={handleFileChange}
          className="hidden"
          aria-label="Upload files"
          disabled={isLoading || isUploading}
          tabIndex={-1}
        />

        {voiceState.isTranscribing ? (
          /* Transcribing UI */
          <>
            {/* Transcribing indicator */}
            <div 
              className="flex-1 flex items-center justify-center gap-3"
              role="status"
              aria-live="polite"
            >
              <Loader 
                className="w-5 h-5 text-studymate-black dark:text-white animate-spin" 
                strokeWidth={3}
                aria-hidden="true"
              />
              <span className="text-base font-medium text-studymate-black dark:text-white">
                Transcribing...
              </span>
            </div>
          </>
        ) : voiceState.isRecording ? (
          /* Recording UI Controls */
          <>
            {/* Pulsing red recording indicator */}
            <div 
              className="flex-shrink-0 mr-3 mb-1 flex items-center"
              role="status"
              aria-label="Recording in progress"
            >
              <div className="relative">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" aria-hidden="true" />
                <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75" aria-hidden="true" />
              </div>
            </div>

            {/* Recording time display */}
            <div className="flex-1 flex items-center justify-center">
              <span 
                className="text-lg font-semibold text-studymate-black dark:text-white tracking-wider"
                role="timer"
                aria-live="off"
                aria-label={`Recording time: ${formatRecordingTime(voiceState.recordingTime)}`}
              >
                {formatRecordingTime(voiceState.recordingTime)}
              </span>
            </div>

            {/* Cancel button (X) */}
            <button
              onClick={handleCancelRecording}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  handleCancelRecording();
                }
              }}
              className="flex-shrink-0 mr-3 mb-1 transition-all duration-200 btn-micro hover:bg-red-100 dark:hover:bg-red-900/30"
              aria-label="Cancel recording (Escape key)"
              title="Cancel recording"
            >
              <X className="w-6 h-6 text-red-500" strokeWidth={3} aria-hidden="true" />
            </button>

            {/* Stop button (Square) */}
            <button
              onClick={handleStopRecording}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleStopRecording();
                }
              }}
              className="flex-shrink-0 mb-1 transition-all duration-200 btn-micro"
              aria-label="Stop recording and transcribe (Enter or Space key)"
              title="Stop recording"
            >
              <Square className="w-6 h-6 text-studymate-black dark:text-white fill-current" strokeWidth={3} aria-hidden="true" />
            </button>
          </>
        ) : (
          /* Normal UI Controls */
          <>
            {/* Plus Icon - File Upload Button */}
            <button
              onClick={handleFileClick}
              disabled={isLoading || isUploading}
              className="flex-shrink-0 mr-3 mb-1 transition-all duration-200 btn-micro disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Attach file (images, PDFs, documents)"
              aria-busy={isUploading}
              aria-disabled={isLoading || isUploading}
              title="Attach file"
            >
              {isUploading ? (
                <Loader 
                  className="w-[26px] h-[26px] text-studymate-black dark:text-white animate-spin" 
                  strokeWidth={3}
                  aria-hidden="true"
                />
              ) : (
                <Plus 
                  className="w-[26px] h-[26px] text-studymate-black dark:text-white" 
                  strokeWidth={3}
                  aria-hidden="true"
                />
              )}
            </button>

            {/* Textarea Field */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask anything"
              disabled={isLoading}
              rows={1}
              className={`flex-1 bg-transparent outline-none ${getTextSizeClass()} text-studymate-darkgray dark:text-gray-300 placeholder:text-studymate-darkgray dark:placeholder:text-gray-500 tracking-[2px] disabled:opacity-50 disabled:cursor-not-allowed transition-all resize-none overflow-y-auto max-h-[100px] leading-relaxed scrollbar-thin scrollbar-thumb-studymate-darkgray dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-studymate-black dark:hover:scrollbar-thumb-gray-500`}
              style={{ fontFamily: "'Exo 2', sans-serif" }}
              aria-label="Message input. Press Enter to send, Shift+Enter for new line"
              aria-multiline="true"
              aria-disabled={isLoading}
              aria-describedby="chat-input-help"
            />
            <span id="chat-input-help" className="sr-only">
              Type your message and press Enter to send. Press Shift+Enter to add a new line. Click the microphone icon to record a voice message.
            </span>

            {/* Send/Microphone Button */}
            <button
              onClick={message.trim() ? handleSend : handleMicrophoneClick}
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  if (message.trim()) {
                    handleSend();
                  } else {
                    handleMicrophoneClick();
                  }
                }
              }}
              className="flex-shrink-0 ml-3 mb-1 transition-all duration-200 btn-micro disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label={
                message.trim() 
                  ? "Send message (Enter key)" 
                  : isVoiceInputSupported()
                    ? "Record voice message"
                    : "Send message (Enter key)"
              }
              aria-busy={isLoading}
              aria-disabled={isLoading}
              title={message.trim() ? "Send message" : "Record voice message"}
            >
              {isLoading ? (
                <Loader 
                  className="w-6 h-6 text-studymate-black dark:text-white animate-spin" 
                  strokeWidth={3}
                  aria-hidden="true"
                />
              ) : message.trim() ? (
                <Send 
                  className="w-6 h-6 text-studymate-black dark:text-white" 
                  strokeWidth={3}
                  aria-hidden="true"
                />
              ) : isVoiceInputSupported() ? (
                <Mic 
                  className="w-6 h-6 text-studymate-black dark:text-white" 
                  strokeWidth={3}
                  aria-hidden="true"
                />
              ) : (
                <Send 
                  className="w-6 h-6 text-studymate-black dark:text-white" 
                  strokeWidth={3}
                  aria-hidden="true"
                />
              )}
            </button>
          </>
        )}
      </div>
    </div>

      {/* Voice Visualizer - shown when recording */}
      <VoiceVisualizer
        isRecording={voiceState.isRecording}
        audioAnalyzer={voiceState.audioAnalyzer}
        recordingTime={voiceState.recordingTime}
      />
    </>
  );
}
