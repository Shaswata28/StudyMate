# Voice Input Chat - Accessibility Testing Guide

This guide helps verify that all accessibility features are working correctly for the voice input chat functionality.

## Automated Tests

Run the test suite to verify basic accessibility:
```bash
npm run test -- ChatInput.test
```

## Manual Keyboard Navigation Tests

### Test 1: Tab Navigation Through Controls
1. Load the chat interface
2. Press Tab repeatedly to navigate through all interactive elements
3. **Expected**: Focus should move through:
   - File upload button (Plus icon)
   - Message textarea
   - Send/Microphone button
   - All buttons should have visible focus indicators

### Test 2: Recording with Keyboard
1. Tab to the microphone button (when input is empty)
2. Press Enter or Space to start recording
3. **Expected**: Recording should start, visualizer appears
4. Press Escape to cancel recording
5. **Expected**: Recording cancels, returns to initial state

### Test 3: Stop Recording with Keyboard
1. Start recording (click microphone or press Enter/Space)
2. Tab to the Stop button (Square icon)
3. Press Enter or Space
4. **Expected**: Recording stops and transcription begins

### Test 4: Cancel Recording with Keyboard
1. Start recording
2. Tab to the Cancel button (X icon)
3. Press Enter or Space (or press Escape from anywhere)
4. **Expected**: Recording cancels without transcription

### Test 5: Error Dismissal with Keyboard
1. Trigger an error (e.g., deny microphone permission)
2. Tab to the Dismiss button (X icon)
3. Press Enter or Space
4. **Expected**: Error message disappears

### Test 6: Retry with Keyboard
1. Trigger an error that allows retry
2. Tab to the Retry button
3. Press Enter or Space
4. **Expected**: Operation retries

### Test 7: Message Input with Keyboard
1. Tab to the message textarea
2. Type a message
3. Press Enter (without Shift)
4. **Expected**: Message sends
5. Type another message
6. Press Shift+Enter
7. **Expected**: New line is added (message doesn't send)

## Screen Reader Tests

### Test 1: ARIA Labels
Use a screen reader (NVDA, JAWS, VoiceOver) to verify:
1. File upload button announces: "Attach file (images, PDFs, documents)"
2. Message textarea announces: "Message input. Press Enter to send, Shift+Enter for new line"
3. Microphone button announces: "Record voice message"
4. Send button announces: "Send message (Enter key)"
5. Stop button announces: "Stop recording and transcribe (Enter or Space key)"
6. Cancel button announces: "Cancel recording (Escape key)"

### Test 2: State Announcements
1. Start recording
2. **Expected**: Screen reader announces "Recording started. Recording time: 00:00"
3. Stop recording
4. **Expected**: Screen reader announces "Transcribing audio, please wait"
5. After transcription completes
6. **Expected**: Focus moves to textarea with transcribed text

### Test 3: Error Announcements
1. Trigger an error (deny microphone permission)
2. **Expected**: Screen reader immediately announces the error message
3. Error should be announced as an alert (assertive)

### Test 4: Recording Timer
1. Start recording
2. **Expected**: Timer updates are NOT announced continuously (aria-live="off")
3. Timer is only announced when focused

### Test 5: Visualizer Dialog
1. Start recording
2. **Expected**: Screen reader announces:
   - "Voice Recording in Progress" (dialog title)
   - "Recording your voice message. The visualizer shows audio levels. Press Escape to cancel or click Stop to finish recording." (description)

## Visual Accessibility Tests

### Test 1: Focus Indicators
1. Navigate with keyboard
2. **Expected**: All focused elements have clear visual indicators
3. Focus indicators should be visible in both light and dark modes

### Test 2: Color Contrast
1. Check error messages in both light and dark modes
2. **Expected**: Text has sufficient contrast ratio (WCAG AA: 4.5:1 for normal text)
3. Icons and buttons are distinguishable

### Test 3: Icon Accessibility
1. Verify all icons have `aria-hidden="true"`
2. **Expected**: Icons are decorative, labels provide context
3. Screen readers should not announce icon names

## Browser Compatibility

Test keyboard navigation and screen reader support in:
- [ ] Chrome + NVDA (Windows)
- [ ] Firefox + NVDA (Windows)
- [ ] Safari + VoiceOver (macOS)
- [ ] Edge + Narrator (Windows)

## Success Criteria

All tests should pass with:
- ✅ All interactive elements are keyboard accessible
- ✅ Focus order is logical and predictable
- ✅ Screen readers announce all state changes
- ✅ ARIA labels are descriptive and helpful
- ✅ Error messages are announced immediately
- ✅ No keyboard traps exist
- ✅ Escape key cancels recording from anywhere
- ✅ Focus management works correctly after transcription

## Known Limitations

- Canvas visualizer is decorative and marked with `role="img"` and descriptive label
- Recording timer updates are not announced continuously to avoid overwhelming screen reader users
- Some browser-specific MediaRecorder API differences may affect functionality
