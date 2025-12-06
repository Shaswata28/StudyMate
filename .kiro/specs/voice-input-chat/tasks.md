# Implementation Plan - Voice Input Chat

- [x] 1. Create backend transcription endpoint







  - Create `/api/transcribe` endpoint in Express server
  - Accept multipart form data with audio file
  - Forward audio to AI Brain service at `http://localhost:8001/router`
  - Include prompt "Transcribe this audio"
  - Return transcribed text or error response
  - Handle errors (network, service unavailable, timeout)
  - _Requirements: 3.1, 5.1, 5.2_

- [ ]* 1.1 Write unit tests for transcription endpoint
  - Test successful transcription flow
  - Test error handling (network errors, service unavailable)
  - Test audio file validation
  - Mock AI Brain service responses
  - _Requirements: 3.1, 3.5, 5.2_

- [x] 2. Add voice recording state management to ChatInput



  - Add voice recording state interface (isRecording, isTranscribing, recordingTime, audioBlob, error, etc.)
  - Implement MediaRecorder API support detection
  - Add state management hooks for recording lifecycle
  - Implement timer for recording duration
  - _Requirements: 1.1, 2.1, 2.3, 7.1_

- [ ]* 2.1 Write property test for icon state
  - **Property 1: Icon state reflects input content**
  - **Validates: Requirements 1.1, 1.2, 1.3**
  - Generate random input states (empty, with text)
  - Verify correct icon is displayed based on input state
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 3. Implement microphone icon and permission handling
  - Replace send icon with microphone icon when input is empty
  - Add click handler to request microphone permissions
  - Handle permission granted/denied states
  - Display error message on permission denial
  - Hide microphone icon if MediaRecorder not supported
  - _Requirements: 1.1, 1.4, 1.5, 7.1_

- [ ]* 3.1 Write unit tests for permission handling
  - Test microphone permission request
  - Test permission denied error display
  - Test MediaRecorder support detection
  - Mock navigator.mediaDevices.getUserMedia
  - _Requirements: 1.4, 1.5, 7.1_

- [ ] 4. Implement audio recording functionality
  - Initialize MediaRecorder with audio stream
  - Collect audio chunks during recording
  - Start recording on microphone icon click
  - Update recording timer every second
  - Create audio blob when recording stops
  - Clean up MediaRecorder and streams properly
  - _Requirements: 2.1, 2.3, 2.5_

- [ ] 5. Implement recording UI controls
  - Display stop icon (Square) when recording
  - Display cancel button (X) when recording
  - Display pulsing red recording indicator
  - Display elapsed recording time
  - Handle stop button click to end recording
  - Handle cancel button click to discard recording
  - _Requirements: 2.2, 2.3, 2.4, 4.1, 4.2_

- [ ]* 5.1 Write property test for recording state UI
  - **Property 2: Recording state controls UI elements**
  - **Validates: Requirements 2.2, 2.3, 2.4, 4.1, 6.1**
  - Generate random recording states
  - Verify all required UI elements are present when recording
  - _Requirements: 2.2, 2.3, 2.4, 4.1_

- [ ] 6. Implement audio transcription integration
  - Send audio blob to `/api/transcribe` endpoint
  - Display loading indicator during transcription
  - Populate input field with transcribed text on success
  - Display error message on transcription failure
  - Allow user to edit transcribed text
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 6.1 Write property test for transcription state
  - **Property 3: Transcription state shows loading indicator**
  - **Validates: Requirements 3.2**
  - Generate random transcription states
  - Verify loading indicator is visible when isTranscribing is true
  - _Requirements: 3.2_

- [ ]* 6.2 Write unit tests for transcription flow
  - Test successful transcription and text population
  - Test transcription error handling
  - Test text editability after transcription
  - Mock fetch API for transcription endpoint
  - _Requirements: 3.3, 3.4, 3.5_

- [ ] 7. Create VoiceVisualizer component
  - Create new component file `client/components/VoiceVisualizer.tsx`
  - Accept props: isRecording, audioAnalyzer, recordingTime
  - Implement circular animated visualizer
  - Display recording timer
  - Use theme colors (studymate-orange/studymate-green)
  - _Requirements: 6.1, 6.4_

- [ ] 8. Implement audio-reactive visualizer animation
  - Set up AudioContext and AnalyserNode when recording starts
  - Use requestAnimationFrame for smooth 60fps animation
  - Read audio amplitude from AnalyserNode
  - Scale visualizer based on amplitude
  - Implement idle animation for low/no audio
  - Clean up AudioContext when recording stops
  - _Requirements: 6.2, 6.3_

- [ ]* 8.1 Write property test for visualizer amplitude response
  - **Property 5: Visualizer responds to audio amplitude**
  - **Validates: Requirements 6.2**
  - Generate random amplitude values
  - Verify visualizer scale correlates with amplitude
  - _Requirements: 6.2_

- [ ]* 8.2 Write property test for visualizer idle state
  - **Property 6: Visualizer idle state**
  - **Validates: Requirements 6.3**
  - Generate amplitude values below threshold
  - Verify idle animation is displayed
  - _Requirements: 6.3_

- [ ]* 8.3 Write property test for visualizer theme colors
  - **Property 7: Theme-aware visualizer colors**
  - **Validates: Requirements 6.4**
  - Generate random theme states (light/dark)
  - Verify correct color is used for each theme
  - _Requirements: 6.4_

- [ ] 9. Integrate VoiceVisualizer into ChatInput
  - Import and render VoiceVisualizer component
  - Pass recording state, audioAnalyzer, and recordingTime as props
  - Position visualizer appropriately in the UI
  - Show visualizer only when recording is active
  - _Requirements: 6.1_

- [ ] 10. Implement audio format handling
  - Detect browser-specific audio formats (webm, ogg, mp4)
  - Handle format conversion if needed
  - Validate audio file size (max 25MB)
  - Display error for oversized files
  - _Requirements: 5.3, 5.4_

- [ ]* 10.1 Write property test for audio format compatibility
  - **Property 4: Audio format compatibility**
  - **Validates: Requirements 5.3, 7.4**
  - Generate audio blobs with different MIME types
  - Verify all formats are handled correctly
  - _Requirements: 5.3, 7.4_

- [ ]* 10.2 Write unit tests for file size validation
  - Test files under 25MB are accepted
  - Test files over 25MB are rejected with error
  - Test edge case at exactly 25MB
  - _Requirements: 5.4_

- [ ] 11. Implement cancel recording functionality
  - Add cancel button UI when recording
  - Stop MediaRecorder on cancel
  - Discard audio chunks and blob
  - Reset all recording state
  - Ensure no API call is made on cancel
  - Return to initial state with microphone icon
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 11.1 Write unit tests for cancel functionality
  - Test recording stops on cancel
  - Test audio data is discarded
  - Test state is reset to initial
  - Test no transcription API call is made
  - _Requirements: 4.2, 4.3, 4.4_

- [ ] 12. Add error handling and user feedback
  - Display permission denied error message
  - Display recording failed error message
  - Display transcription failed error message
  - Display service unavailable error message
  - Display file too large error message
  - Add retry capability for failed operations
  - _Requirements: 1.5, 3.5, 5.2_

- [ ] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Add accessibility features
  - Add ARIA labels to all interactive elements
  - Ensure keyboard navigation works
  - Add screen reader announcements for state changes
  - Test with keyboard-only navigation
  - _Requirements: All_

- [ ] 15. Cross-browser testing and polish
  - Test in Chrome, Firefox, Safari, Edge
  - Verify MediaRecorder API compatibility
  - Test audio format handling across browsers
  - Verify visualizer animations are smooth
  - Fix any browser-specific issues
  - _Requirements: 7.1, 7.3_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
