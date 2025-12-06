import { Plus, Send, Loader, Mic } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import VoiceVisualizer from "./VoiceVisualizer";

interface ChatInputProps {
  onSend?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  isLoading?: boolean;
}

interface VoiceRecordingState {
  isRecording: boolean;
  recordingTime: number;
  error: string | null;
  errorType: 'permission' | 'recognition' | 'not-supported' | null;
  canRetry: boolean;
  recognition: any | null;
  transcript: string;
  audioAnalyzer: AnalyserNode | null;
}

export default function ChatInput({ onSend, onFileUpload, isLoading = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Refs for safety
  const isRecordingRef = useRef(false);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const [voiceState, setVoiceState] = useState<VoiceRecordingState>({
    isRecording: false,
    recordingTime: 0,
    error: null,
    errorType: null,
    canRetry: false,
    recognition: null,
    transcript: "",
    audioAnalyzer: null,
  });

  const isVoiceInputSupported = () => {
    return !!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
  };

  const stopCleanup = () => {
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }
    if (audioContextRef.current) {
      try { audioContextRef.current.close(); } catch (e) {}
      audioContextRef.current = null;
    }
  };

  const startRecording = async () => {
    // 1. Safety check: Stop any existing instance first
    if (voiceState.recognition) {
        voiceState.recognition.onend = null;
        voiceState.recognition.abort();
    }
    stopCleanup();

    if (!isVoiceInputSupported()) {
      setVoiceState(prev => ({ ...prev, error: "Not supported", errorType: 'not-supported' }));
      return;
    }

    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      // Audio Visualizer Setup
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioStreamRef.current = stream;
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const audioContext = new AudioContextClass();
        audioContextRef.current = audioContext;
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        setVoiceState(prev => ({ ...prev, audioAnalyzer: analyser }));
      } catch (err) {
        console.warn("Visualizer failed:", err);
      }

      isRecordingRef.current = true;

      // CRITICAL: Real-time Transcript Logic - Rebuild string every result
      recognition.onresult = (event: any) => {
        let fullTranscript = '';
        
        for (let i = 0; i < event.results.length; i++) {
          fullTranscript += event.results[i][0].transcript;
        }

        setVoiceState(prev => ({
          ...prev,
          transcript: fullTranscript
        }));
      };

      recognition.onerror = (event: any) => {
        if (event.error === 'no-speech' || event.error === 'aborted') return;
        if (!isRecordingRef.current) return;

        console.error('Speech error:', event.error);
        isRecordingRef.current = false;
        setVoiceState(prev => ({
          ...prev,
          isRecording: false,
          error: "Voice recognition failed",
          errorType: 'recognition',
          canRetry: true
        }));
        stopCleanup();
      };

      recognition.onend = () => {
        if (isRecordingRef.current) {
            try { recognition.start(); } catch (e) {}
        } else {
            setVoiceState(prev => ({ ...prev, isRecording: false }));
        }
      };

      recognition.start();

      setVoiceState(prev => ({
        ...prev,
        isRecording: true,
        recognition,
        transcript: "",
        error: null,
        canRetry: false
      }));

    } catch (error) {
      isRecordingRef.current = false;
      setVoiceState(prev => ({ ...prev, error: "Failed to start", canRetry: true }));
    }
  };

  const stopRecording = () => {
    isRecordingRef.current = false;
    if (voiceState.recognition) {
      voiceState.recognition.onend = null;
      voiceState.recognition.stop();
    }
    stopCleanup();
    setMessage(voiceState.transcript); // Transfer final text to input
    setVoiceState(prev => ({ ...prev, isRecording: false }));
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const cancelRecording = () => {
    isRecordingRef.current = false;
    if (voiceState.recognition) {
      voiceState.recognition.onend = null; // Prevent restart loop
      voiceState.recognition.abort();      // Hard stop
    }
    stopCleanup();
    setVoiceState({
      isRecording: false,
      recordingTime: 0,
      error: null,
      errorType: null,
      canRetry: false,
      recognition: null,
      transcript: "",
      audioAnalyzer: null,
    });
  };

  const handleRetryRecording = () => {
    isRecordingRef.current = false;
    if (voiceState.recognition) {
        voiceState.recognition.onend = null;
        voiceState.recognition.abort();
    }
    stopCleanup();
    
    setVoiceState(prev => ({ ...prev, transcript: "", isRecording: false }));
    
    setTimeout(() => {
        startRecording();
    }, 300);
  };

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
  
  // Adaptive Height Logic: This runs whenever the message state changes.
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      // Sets height to fit scroll content, but caps it at 100px (max-h-[100px] CSS class)
      textarea.style.height = `${Math.min(textarea.scrollHeight, 100)}px`;
    }
  }, [message]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isRecordingRef.current = false;
      if (voiceState.recognition) {
          voiceState.recognition.onend = null;
          voiceState.recognition.abort();
      }
      stopCleanup();
    };
  }, [voiceState.recognition]);


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
        onFileUpload?.(Array.from(e.target.files));
        e.target.value = "";
    }
  };

  return (
    <>
      <div className="w-full max-w-[609px] mx-auto">
        {/* Error Display */}
        {voiceState.error && (
          <div className="mb-2 px-4 py-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
             <p className="text-red-600 dark:text-red-400 text-sm">{voiceState.error}</p>
          </div>
        )}
        
        <div className="relative flex items-end bg-studymate-gray dark:bg-slate-800 rounded-[26px] shadow-lg min-h-[52px] px-4 py-3 transition-all duration-200 border border-transparent dark:border-slate-700 hover:shadow-xl">
            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />

            {/* Plus Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isUploading || voiceState.isRecording}
              className="flex-shrink-0 mr-3 mb-1 transition-all duration-200 btn-micro disabled:opacity-50"
            >
              {isLoading || isUploading ? <Loader className="w-[26px] h-[26px] animate-spin" /> : <Plus className="w-[26px] h-[26px]" />}
            </button>

            {/* Textarea (Adaptive element) */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={voiceState.isRecording ? "Listening..." : "Ask anything"}
              disabled={isLoading || voiceState.isRecording}
              rows={1}
              className="flex-1 bg-transparent outline-none text-xl text-studymate-darkgray dark:text-gray-300 placeholder:text-studymate-darkgray dark:placeholder:text-gray-500 tracking-[2px] disabled:opacity-50 transition-all resize-none overflow-y-auto max-h-[100px] leading-relaxed scrollbar-hide"
              style={{ fontFamily: "'Exo 2', sans-serif" }}
            />

            {/* Send/Mic Button */}
            <button
              onClick={message.trim() ? handleSend : startRecording}
              disabled={isLoading || voiceState.isRecording}
              className="flex-shrink-0 ml-3 mb-1 transition-all duration-200 btn-micro disabled:opacity-50"
            >
              {isLoading ? <Loader className="w-6 h-6 animate-spin" /> : message.trim() ? <Send className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
            </button>
        </div>
      </div>

      <VoiceVisualizer
        isRecording={voiceState.isRecording}
        audioAnalyzer={voiceState.audioAnalyzer}
        transcript={voiceState.transcript}
        onStop={stopRecording}
        onCancel={cancelRecording}
        onRetry={handleRetryRecording}
      />
    </>
  );
}