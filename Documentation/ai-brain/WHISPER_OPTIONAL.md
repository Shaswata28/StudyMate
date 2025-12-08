# Whisper Audio Transcription - Optional Feature

## Overview

The AI Brain Service now works **without Whisper** being fully loaded. Audio transcription is an optional feature that can be enabled later.

## Current Status

✅ **Brain service starts immediately** - No waiting for Whisper download
✅ **Text generation works** - Qwen 2.5 1.5B for chat
✅ **Image OCR works** - DeepSeek OCR for vision
✅ **Embeddings work** - mxbai-embed-large for vectors
⏳ **Audio transcription** - Disabled until Whisper loads

## How It Works

1. **On startup**: Brain service tries to load Whisper
2. **If Whisper loads**: Audio transcription enabled ✓
3. **If Whisper fails**: Service continues without audio support
4. **Audio requests**: Skipped gracefully with a warning log

## Enabling Audio Support

### Option 1: Let it download in background (Recommended)

Just start the brain service - Whisper will download automatically:

```bash
cd ai-brain
python brain.py
```

The first time will download ~3GB (10-30 minutes depending on internet speed).
Subsequent starts will be fast (~10 seconds).

### Option 2: Pre-download Whisper

Download the model before starting the service:

```bash
cd ai-brain
python -c "import whisper; whisper.load_model('large-v3')"
```

### Option 3: Use a smaller model

Edit `brain.py` and change `large-v3` to `base`:

```python
whisper_model = whisper.load_model("base")  # Only 140MB
```

## Checking Audio Status

Visit the health endpoint:

```bash
curl http://localhost:8001/
```

Response:
```json
{
  "status": "Active",
  "core_model": "qwen2.5:1.5b",
  "mode": "Persistent Core",
  "whisper_loaded": true  // or false
}
```

## Model Sizes

| Model | Size | Accuracy | RAM Usage |
|-------|------|----------|-----------|
| tiny | 39MB | Basic | ~1GB |
| base | 140MB | Good | ~1GB |
| small | 460MB | Better | ~2GB |
| medium | 1.4GB | Great | ~5GB |
| large-v3 | 2.9GB | Best | ~6GB |

## Troubleshooting

**Whisper download stuck?**
- Cancel (Ctrl+C) and restart - it will resume
- Or use a smaller model (see Option 3 above)

**Want to skip audio entirely?**
- Just start the brain service - it will work without Whisper
- Audio requests will be logged and skipped

**Check if Whisper is cached:**
```powershell
dir $env:USERPROFILE\.cache\whisper
```

You should see `large-v3.pt` (~3GB) if downloaded.
