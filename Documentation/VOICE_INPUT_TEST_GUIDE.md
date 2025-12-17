# Voice Input Testing Guide

## Quick Test

1. **Start the services:**
   ```bash
   # Terminal 1: Start AI Brain
   cd ai-brain
   python brain.py

   # Terminal 2: Start Python Backend
   cd python-backend
   uvicorn main:app --reload --port 8000

   # Terminal 3: Start Frontend
   pnpm dev
   ```

2. **Open the app** in Chrome, Edge, or Safari (not Firefox)

3. **Test voice input:**
   - Click the microphone icon in the chat input
   - Allow microphone access when prompted
   - Speak clearly: "Hello, can you help me with my studies?"
   - Watch the text appear in real-time as you speak
   - Click the stop button (square icon) when done
   - The text should be in the input field
   - Press Enter or click Send to send to AI

## Expected Behavior

### ✅ Success Indicators
- Microphone icon appears when input is empty
- Clicking mic shows recording UI with timer
- Text appears in real-time as you speak
- Stop button ends recording and keeps text
- Cancel button (X) discards recording
- Text is sent to AI Brain for processing

### ❌ Common Issues

**"Voice input is not supported"**
- You're using Firefox (not supported)
- Solution: Use Chrome, Edge, or Safari

**"Microphone permission denied"**
- Browser blocked microphone access
- Solution: Click the lock icon in address bar → Allow microphone

**"No speech detected"**
- Microphone not working or too quiet
- Solution: Check microphone settings, speak louder

**"Network error"**
- No internet connection (Chrome/Edge need internet for speech recognition)
- Solution: Check internet connection

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Uses Google's servers |
| Edge | ✅ Full | Uses Google's servers |
| Safari | ✅ Full | On-device processing (more private) |
| Firefox | ❌ None | No Web Speech API support |

## Privacy Notes

- **Chrome/Edge**: Audio sent to Google for transcription
- **Safari**: Processing happens on-device (more private)
- **All browsers**: Final text sent to your local AI Brain

## Troubleshooting

### Microphone not working
1. Check system microphone settings
2. Check browser permissions
3. Try a different browser
4. Restart browser

### Text not appearing
1. Check browser console for errors (F12)
2. Ensure you're speaking clearly
3. Check microphone volume
4. Try refreshing the page

### Recognition stops unexpectedly
- This is normal - Web Speech API has timeouts
- Just click the mic button again to continue

## Advanced Testing

### Test different scenarios:
- Short phrases
- Long sentences
- Technical terms
- Numbers and dates
- Punctuation (say "comma", "period", etc.)
- Different accents

### Test error handling:
- Deny microphone permission
- Disconnect internet (Chrome/Edge)
- Switch to Firefox
- Cancel mid-recording

## Comparison: Old vs New

### Old (Whisper)
- ❌ 3-5 second delay
- ❌ 3GB model download
- ❌ Backend processing required
- ✅ Works offline
- ✅ More accurate with technical terms

### New (Web Speech API)
- ✅ Instant, real-time transcription
- ✅ No downloads needed
- ✅ No backend load
- ❌ Requires internet (Chrome/Edge)
- ❌ Less accurate with technical terms

## Success!

If you can speak and see text appear in real-time, the migration is successful! 🎉
