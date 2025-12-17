# Design Document

## Overview

This design document outlines the architecture for migrating from Google Gemini API to a local AI brain service. The solution consists of two main components:

1. **AI Brain Service**: A standalone FastAPI application that manages local AI models (Qwen 2.5 1.5B, DeepSeek OCR, Whisper Turbo, mxbai-embed-large) and provides a unified API for AI operations
2. **Main Backend Integration**: Modified chat and AI-related endpoints that communicate with the brain service instead of Gemini API

The brain service will be automatically started as a subprocess when the main backend launches, ensuring seamless operation without manual process management.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Backend (Port 5000)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Brain Process Manager                                  │ │
│  │  - Starts brain service on backend startup             │ │
│  │  - Monitors brain health                               │ │
│  │  - Terminates brain on shutdown                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Local AI Service (replaces gemini_service.py)        │ │
│  │  - HTTP client to brain service                        │ │
│  │  - Request formatting and error handling               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Chat Router                                           │ │
│  │  - Uses local_ai_service instead of gemini_service    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP (localhost:8001)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Brain Service (Port 8001)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Application                                   │ │
│  │  - /router (text, image, audio)                        │ │
│  │  - /utility/embed (embeddings)                         │ │
│  │  - / (health check)                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Model Manager                                         │ │
│  │  - Persistent: Qwen 2.5 1.5B (always loaded)          │ │
│  │  - Temporary: DeepSeek OCR (load on demand)           │ │
│  │  - Temporary: mxbai-embed-large (load on demand)      │ │
│  │  - RAM: Whisper Turbo (loaded at startup)             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  VRAM Cleanup Manager                                  │ │
│  │  - Unloads temporary models after use                 │ │
│  │  - Clears CUDA cache                                   │ │
│  │  - Triggers garbage collection                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Ollama API (localhost:11434)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ollama Service                            │
│  - qwen2.5:1.5b (text generation)                           │
│  - deepseek-ocr (vision/OCR)                                │
│  - mxbai-embed-large (embeddings)                           │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

#### Text Generation Flow
1. Client sends chat request to main backend `/api/chat`
2. Main backend forwards to brain service `/router` with text prompt
3. Brain service uses persistent Qwen 2.5 1.5B model (already in VRAM)
4. Response generated and returned immediately
5. Qwen stays loaded for next request

#### Image OCR Flow
1. Client sends image to main backend
2. Main backend forwards to brain service `/router` with image file
3. Brain service loads DeepSeek OCR model
4. Image processed and text extracted
5. DeepSeek OCR unloaded from VRAM
6. Extracted text returned

#### Audio Transcription Flow
1. Client sends audio to main backend
2. Main backend forwards to brain service `/router` with audio file
3. Brain service uses Whisper Turbo (in RAM) to transcribe
4. Transcribed text used as prompt for Qwen 2.5 1.5B
5. AI response generated and returned

#### Embedding Generation Flow
1. Main backend needs embeddings for text
2. Request sent to brain service `/utility/embed`
3. Brain service loads mxbai-embed-large
4. Embedding vector generated
5. Model unloaded immediately
6. Vector returned

## Components and Interfaces

### AI Brain Service (ai-brain/brain.py)

**FastAPI Endpoints:**

```python
@app.get("/")
def home() -> dict
    # Returns service status and configuration
    
@app.post("/router")
async def intelligent_router(
    prompt: str = Form(...),
    image: UploadFile = File(None),
    audio: UploadFile = File(None)
) -> dict
    # Routes request to appropriate model
    # Returns: {"response": str, "model": str}
    
@app.post("/utility/embed")
async def process_embedding(text: str) -> dict
    # Generates embedding vector
    # Returns: {"embedding": List[float]}
```

**Internal Functions:**

```python
def cleanup_temporary_resources(model_name: str = None) -> None
    # Unloads specialist models and clears VRAM
    # Never unloads Qwen 2.5 1.5B
```

### Main Backend Integration

**Brain Process Manager (python-backend/services/brain_manager.py)**

```python
class BrainProcessManager:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.brain_url: str = "http://localhost:8001"
        
    async def start_brain(self) -> bool:
        # Starts brain service as subprocess
        # Waits for health check to pass
        # Returns True if successful
        
    async def stop_brain(self) -> None:
        # Gracefully terminates brain subprocess
        
    async def is_healthy(self) -> bool:
        # Checks if brain service is responding
        
    async def restart_brain(self) -> bool:
        # Stops and restarts brain service
```

**Local AI Service (python-backend/services/local_ai_service.py)**

```python
class LocalAIService:
    def __init__(self, brain_url: str = "http://localhost:8001"):
        self.brain_url = brain_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def generate_response(
        self,
        message: str,
        history: Optional[List[Message]] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        # Sends request to brain service /router
        # Handles text, image, and audio attachments
        # Returns AI response text
        
    async def generate_embedding(self, text: str) -> List[float]:
        # Sends request to brain service /utility/embed
        # Returns embedding vector
        
    async def health_check(self) -> bool:
        # Checks if brain service is available
```

**Modified Chat Router (python-backend/routers/chat.py)**

- Replace `gemini_service` imports with `local_ai_service`
- Update error handling for brain service errors
- Maintain same endpoint signatures and responses

### Startup Integration (python-backend/main.py)

```python
from services.brain_manager import brain_manager

@app.on_event("startup")
async def startup_event():
    # Start brain service
    success = await brain_manager.start_brain()
    if not success:
        logger.warning("Brain service failed to start - AI features disabled")
    
@app.on_event("shutdown")
async def shutdown_event():
    # Stop brain service
    await brain_manager.stop_brain()
```

## Data Models

### Brain Service Request/Response

```python
# Router Request (multipart/form-data)
{
    "prompt": str,           # Required
    "image": UploadFile,     # Optional
    "audio": UploadFile      # Optional
}

# Router Response
{
    "response": str,         # AI generated text
    "model": str            # Model used (e.g., "qwen2.5:1.5b")
}

# Embed Request
{
    "text": str             # Text to embed
}

# Embed Response
{
    "embedding": List[float]  # Vector representation
}

# Health Check Response
{
    "status": str,           # "Active"
    "core_model": str,       # "qwen2.5:1.5b"
    "mode": str             # "Persistent Core"
}
```

### Main Backend Models

Existing models remain unchanged:
- `ChatRequest`: User message with optional history and attachments
- `ChatResponse`: AI response with timestamp
- `Message`: Role and content for chat history
- `Attachment`: File attachment with type and data

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Text generation returns valid response structure
*For any* text prompt sent to /router, the response should contain both "response" (string) and "model" (string) fields
**Validates: Requirements 2.3**

Property 2: Qwen model persistence
*For any* sequence of text generation requests, the Qwen 2.5 1.5B model should remain loaded in memory after each request completes
**Validates: Requirements 2.2**

Property 3: Concurrent text request handling
*For any* set of concurrent text requests, all requests should receive valid responses using the persistent Qwen model
**Validates: Requirements 2.5**

Property 4: Image processing triggers OCR model loading
*For any* image file sent to /router, the DeepSeek OCR model should be loaded before processing
**Validates: Requirements 3.1**

Property 5: OCR extraction completeness
*For any* image containing text, the OCR response should extract and return text content
**Validates: Requirements 3.2**

Property 6: Specialist model cleanup
*For any* image or embedding request, the specialist model (DeepSeek OCR or mxbai-embed-large) should be unloaded after processing completes
**Validates: Requirements 3.3, 5.3, 6.1**

Property 7: Image response structure
*For any* image processing request, the response should contain both extracted text and the model name "deepseek-ocr"
**Validates: Requirements 3.4**

Property 8: Audio transcription flow
*For any* audio file sent to /router, the system should transcribe it using Whisper and use the transcribed text as the prompt for Qwen
**Validates: Requirements 4.2, 4.3**

Property 9: Temporary audio file handling
*For any* audio request, the system should create a temporary file, process it, and the file should be accessible during processing
**Validates: Requirements 4.1**

Property 10: Embedding model lifecycle
*For any* embedding request to /utility/embed, the mxbai-embed-large model should be loaded with keep_alive=0 and unloaded immediately after generation
**Validates: Requirements 5.1, 5.2, 5.3**

Property 11: Embedding vector format
*For any* text sent to /utility/embed, the response should contain an "embedding" field with a list of floating-point numbers
**Validates: Requirements 5.4**

Property 12: VRAM cleanup completeness
*For any* specialist model unload operation, the system should send keep_alive=0 to Ollama, clear CUDA cache, and trigger garbage collection
**Validates: Requirements 6.2, 6.3, 6.4**

Property 13: Core model protection
*For any* cleanup operation, the Qwen 2.5 1.5B model should never be unloaded
**Validates: Requirements 6.5**

Property 14: Brain service communication
*For any* AI request from the main backend, the request should be sent to http://localhost:8001
**Validates: Requirements 7.1**

Property 15: Attachment type handling
*For any* request with attachments (text, image, or audio), the brain service should correctly process the attachment type
**Validates: Requirements 7.3**

Property 16: Operation logging
*For any* operation (start, complete, or fail), the system should log the operation type and relevant details
**Validates: Requirements 8.1, 8.2, 8.3**

Property 17: Model operation logging
*For any* model load or unload operation, the system should log the model name and the action performed
**Validates: Requirements 8.4**

## Error Handling

### Brain Service Errors

1. **Model Loading Failures**
   - Log error with model name
   - Return 500 error with details
   - Continue with available models

2. **Ollama Connection Failures**
   - Detect on startup
   - Log clear error message
   - Exit with error code

3. **VRAM Exhaustion**
   - Cleanup temporary models aggressively
   - Log memory status
   - Return 503 Service Unavailable

4. **File Processing Errors**
   - Log file type and error
   - Return error in response
   - Clean up temporary files

### Main Backend Errors

1. **Brain Service Unavailable**
   - Return 503 Service Unavailable
   - Log connection error
   - Provide user-friendly message

2. **Brain Service Timeout**
   - Set 60-second timeout
   - Return 504 Gateway Timeout
   - Log timeout details

3. **Brain Service Startup Failure**
   - Log warning on backend startup
   - Disable AI endpoints
   - Return 503 for AI requests

4. **Brain Service Crash**
   - Detect via health checks
   - Attempt automatic restart
   - Log crash details

## Testing Strategy

### Unit Tests

1. **Brain Service Tests**
   - Test each endpoint with valid inputs
   - Test error handling for invalid inputs
   - Test model loading and unloading
   - Test VRAM cleanup

2. **Brain Manager Tests**
   - Test subprocess startup and shutdown
   - Test health check logic
   - Test restart functionality
   - Mock subprocess for testing

3. **Local AI Service Tests**
   - Test request formatting
   - Test response parsing
   - Test error handling
   - Mock HTTP client

4. **Integration Tests**
   - Test full request flow from chat endpoint to brain
   - Test attachment handling (text, image, audio)
   - Test error propagation
   - Test concurrent requests

### Manual Testing

1. Start backend and verify brain service starts automatically
2. Send text chat requests and verify responses
3. Upload image and verify OCR extraction
4. Upload audio and verify transcription
5. Stop backend and verify brain service stops
6. Test error scenarios (Ollama not running, invalid files)

## Deployment Considerations

### Development Environment

- Brain service runs on localhost:8001
- Main backend runs on localhost:5000
- Ollama runs on localhost:11434
- All services on same machine

### Production Environment

- Same port configuration
- Ensure Ollama service is running
- Monitor VRAM usage
- Set up process monitoring (systemd, supervisor)
- Configure automatic restart on failure

### Resource Requirements

- **VRAM**: Minimum 8GB for Qwen 2.5 1.5B + temporary models
- **RAM**: Minimum 4GB for Whisper Turbo
- **CPU**: Multi-core recommended for concurrent requests
- **Storage**: ~10GB for all models

### Installation Steps

1. Install Ollama
2. Pull required models (qwen2.5:1.5b, deepseek-ocr, mxbai-embed-large)
3. Install Python dependencies (fastapi, uvicorn, ollama, whisper, torch)
4. Configure brain service path in main backend
5. Start main backend (brain starts automatically)

## Migration Path

### Phase 1: Setup Brain Service
1. Create ai-brain directory structure
2. Implement brain.py with all endpoints
3. Create requirements.txt and install script
4. Test brain service independently

### Phase 2: Implement Brain Manager
1. Create brain_manager.py with subprocess management
2. Integrate with main backend startup/shutdown
3. Implement health checks and restart logic
4. Test automatic startup and shutdown

### Phase 3: Create Local AI Service
1. Implement local_ai_service.py as Gemini replacement
2. Match Gemini service interface
3. Add attachment handling
4. Test all request types

### Phase 4: Update Chat Router
1. Replace gemini_service with local_ai_service
2. Update error handling
3. Test all chat endpoints
4. Verify chat history still works

### Phase 5: Remove Gemini Dependencies
1. Remove gemini_service.py
2. Remove google-generativeai from requirements
3. Remove GEMINI_API_KEY from environment
4. Update documentation

### Phase 6: Testing and Validation
1. Run full test suite
2. Manual testing of all features
3. Performance testing
4. Error scenario testing
