# Voice Input Chat Feature - Design Document

## Overview

This feature adds voice recording and transcription capabilities to the chat interface. Users can record audio messages that are automatically transcribed to text using the AI Brain's Whisper integration. The feature includes an animated voice visualizer that responds to audio input, providing engaging visual feedback during recording.

The implementation extends the existing ChatInput component with voice recording capabilities, integrates with the AI Brain service for transcription, and adds a new VoiceVisualizer component for animated feedback.

## Architecture

### Component Structure

```
ChatInput (Modified)
├── Voice Recording State Management
├── MediaRecorder Integration
├── Audio Processing Logic
└── VoiceVisualizer (New Component)
    └── Audio-reactive Animation

Backend API (New Endpoint)
└── /api/transcribe
    └── Proxies to AI Brain /router endpoint
```

### Data Flow

1. **Recording Initiation**:
   - User clicks microphone icon
   - Browser requests microphone permissions
   - MediaRecorder API starts capturing audio
   - VoiceVisualizer begins animating

2. **Recording Active**:
   - Audio chunks are collected in memory
   - Audio analyzer provides real-time amplitude data
   - VoiceVisualizer pulses based on voice amplitude
   - Timer displays elapsed recording time

3. **Recording Stop**:
   - MediaRecorder stops and finalizes audio blob
   - Audio blob is sent to backend /api/transcribe endpoint
   - Backend forwards to AI Brain /router endpoint
   - Transcribed text populates input field
   - User can edit before sending

4. **Recording Cancel**:
   - MediaRecorder stops
   - Audio data is discarded
   - Component returns to initial state

## Components and Interfaces

### 1. ChatInput Component (Modified)

**New State Variables**:
```typescript
interface VoiceRecordingState {
  isRecording: boolean;
  isPaused: boolean;
  isTranscribing: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  error: string | null;
  mediaRecorder: MediaRecorder | null;
  audioChunks: Blob[];
  audioAnalyzer: AnalyserNode | null;
}
```

**New Props**:
```typescript
interface ChatInputProps {
  onSend?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  isLoading?: boolean;
  // No new props needed - voice input is built-in
}
```

**New Methods**:
```typescript
// Start recording audio
const startRecording = async (): Promise<void>

// Stop recording and transcribe
const stopRecording = async (): Promise<void>

// Cancel recording without transcribing
const cancelRecording = (): void

// Send audio to backend for transcription
const transcribeAudio = async (audioBlob: Blob): Promise<string>

// Check if browser supports MediaRecorder
const isVoiceInputSupported = (): boolean
```

### 2. VoiceVisualizer Component (New)

**Props**:
```typescript
interface VoiceVisualizerProps {
  isRecording: boolean;
  audioAnalyzer: AnalyserNode | null;
  recordingTime: number;
}
```

**Functionality**:
- Displays circular animated visualizer
- Pulses/expands based on audio amplitude
- Shows recording timer
- Uses theme colors (studymate-orange/studymate-green)
- Smooth 60fps animations using requestAnimationFrame

### 3. Backend API Endpoint (New)

**Endpoint**: `POST /api/transcribe`

**Request**:
```typescript
// Multipart form data
{
  audio: File  // Audio blob from frontend
}
```

**Response**:
```typescript
{
  text: string;  // Transcribed text
  success: boolean;
  error?: string;
}
```

**Implementation**:
- Receives audio file from frontend
- Forwards to AI Brain service at `http://localhost:8001/router`
- Includes prompt: "Transcribe this audio"
- Returns transcribed text to frontend

## Data Models

### Audio Recording Data

```typescript
interface AudioRecording {
  blob: Blob;
  mimeType: string;
  duration: number;
  size: number;
}
```

### Transcription Request

```typescript
interface TranscriptionRequest {
  audio: File;
}
```

### Transcription Response

```typescript
interface TranscriptionResponse {
  text: string;
  success: boolean;
  error?: string;
  model?: string;  // From AI Brain response
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

