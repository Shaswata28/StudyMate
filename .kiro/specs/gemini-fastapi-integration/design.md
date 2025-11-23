# Design Document

## Overview

This design outlines the integration of Google's Gemini API into the StudyMate application through a Python FastAPI backend service. The system will replace the current mock AI responses with real Gemini-powered conversations while maintaining the existing UI components and Express server for other functionality.

### Architecture Goals

- Minimal changes to existing React UI components
- Clean separation between Express (existing routes) and FastAPI (AI chat)
- Simple, maintainable Python backend focused on Gemini integration
- Rate limiting to stay within free tier API quotas
- Proper error handling with user-friendly feedback

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ChatContainer│  │  ChatInput   │  │ ChatMessage  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                          │                                  │
│                          │ HTTP POST /api/chat             │
└──────────────────────────┼─────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Rate Limiter Middleware                             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/chat Endpoint                                  │  │
│  │  - Validate request                                  │  │
│  │  - Format conversation history                       │  │
│  │  - Call Gemini API                                   │  │
│  │  - Return response                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
                    ┌──────────────────┐
                    │   Gemini API     │
                    │  (Google Cloud)  │
                    └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           Express Server (Port 8080)                        │
│  - Serves React frontend                                    │
│  - Handles existing API routes (/api/ping, /api/demo)      │
│  - Proxies /api/chat to FastAPI (development only)          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.10+
- FastAPI (web framework)
- google-generativeai (Gemini SDK)
- slowapi (rate limiting)
- pydantic (data validation)
- uvicorn (ASGI server)

**Frontend (No Changes):**
- React 18
- TypeScript
- Existing chat components

**Existing Backend (Minimal Changes):**
- Express
- Add proxy configuration for development

## Components and Interfaces

### 1. FastAPI Backend Service

**File Structure:**
```
python-backend/
├── main.py                 # FastAPI app entry point
├── routers/
│   └── chat.py            # Chat endpoint
├── services/
│   └── gemini_service.py  # Gemini API integration
├── middleware/
│   └── rate_limiter.py    # Rate limiting logic
├── models/
│   └── schemas.py         # Pydantic models
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

### 2. API Endpoints

#### POST /api/chat

**Request Schema:**
```typescript
{
  "message": string,           // User's message
  "history": Array<{           // Conversation history (optional)
    "role": "user" | "model",
    "content": string
  }>
}
```

**Response Schema (Success):**
```typescript
{
  "response": string,          // AI response text
  "timestamp": string          // ISO 8601 timestamp
}
```

**Response Schema (Error):**
```typescript
{
  "error": string,             // User-friendly error message
  "code": string               // Error code (e.g., "RATE_LIMIT_EXCEEDED")
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (validation error)
- 429: Rate limit exceeded
- 500: Internal server error
- 503: Gemini API unavailable

### 3. Frontend Integration

**Dashboard.tsx Changes:**

The `handleSendMessage` function will be updated to:
1. Call FastAPI backend at `http://localhost:8000/api/chat` (dev) or configured production URL
2. Include conversation history (last 10 messages)
3. Handle error responses by displaying them as AI messages
4. Maintain existing loading state behavior

**No changes needed to:**
- ChatContainer.tsx
- ChatInput.tsx
- ChatMessage.tsx (already handles markdown)

### 4. Rate Limiting Strategy

**Implementation:**
- Use `slowapi` library with in-memory storage
- Default limit: 15 requests per minute per IP address
- Configurable via environment variables
- Returns HTTP 429 with retry-after header

**Rate Limit Configuration:**
```python
RATE_LIMIT_REQUESTS = 15      # requests
RATE_LIMIT_WINDOW = 60        # seconds
```

### 5. Gemini API Integration

**Model Selection:**
- Use `gemini-1.5-flash` (free tier, fast responses)
- Fallback to `gemini-pro` if flash unavailable

**Configuration:**
```python
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_OUTPUT_TOKENS = 1024
GEMINI_TIMEOUT = 30  # seconds
```

**Conversation History Management:**
- Keep last 10 messages (5 exchanges)
- Format: Gemini's native format (role: "user" | "model")
- Sliding window: drop oldest messages when limit exceeded

## Data Models

### Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Message(BaseModel):
    role: Literal["user", "model"]
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[Message]] = Field(default_factory=list, max_length=10)

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class ErrorResponse(BaseModel):
    error: str
    code: str
```

### Frontend Types (Existing)

```typescript
interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
}
```

## Error Handling

### Error Categories

1. **Validation Errors (400)**
   - Empty message
   - Message too long (>2000 chars)
   - Invalid history format
   - Response: Detailed field-level errors

2. **Rate Limit Errors (429)**
   - Too many requests from same IP
   - Response: "You've reached the message limit. Please try again in a moment."

3. **Gemini API Errors (500/503)**
   - API key invalid
   - API quota exceeded
   - Network timeout
   - Response: "I'm having trouble connecting right now. Please try again."

4. **Server Errors (500)**
   - Unexpected exceptions
   - Response: "Something went wrong. Please try again."

### Error Handling Flow

```python
try:
    # Validate request
    # Check rate limit
    # Call Gemini API
    # Return response
except ValidationError:
    return 400 with field errors
except RateLimitExceeded:
    return 429 with retry message
except GeminiAPIError:
    log error details
    return 503 with user-friendly message
except Exception:
    log full traceback
    return 500 with generic message
```

### Frontend Error Display

All errors will be displayed as AI messages in the chat:
```typescript
const errorMessage: Message = {
  id: Date.now().toString(),
  text: errorResponse.error,
  isAI: true,
  timestamp: new Date()
};
setMessages(prev => [...prev, errorMessage]);
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Request-Response Round Trip

*For any* valid user message, when sent from the Chat Client to the FastAPI Backend, the backend should forward it to the Gemini API and return the Gemini response to the client with proper structure.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Rate Limiting Enforcement

*For any* sequence of requests from the same IP address, when the configured rate limit is exceeded, the FastAPI Backend should reject subsequent requests with HTTP 429 status without calling the Gemini API until the time window resets.

**Validates: Requirements 2.2**

### Property 3: Conversation History Management

*For any* conversation with message history, when a new message is sent, the Chat Client should include previous messages in the request, and the FastAPI Backend should format them according to Gemini's requirements, keeping only the most recent 10 messages using a sliding window.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Message Ordering Invariant

*For any* sequence of messages in a conversation, the system should preserve the chronological order and correct role attribution (user vs AI) throughout the entire message lifecycle.

**Validates: Requirements 3.5**

### Property 5: Request Validation

*For any* incoming request payload, the FastAPI Backend should validate it against the defined schema, accepting valid requests and rejecting invalid requests with HTTP 422 status and detailed field-level error messages.

**Validates: Requirements 4.3, 4.5**

### Property 6: CORS Origin Enforcement

*For any* HTTP request to the FastAPI Backend, only requests from configured allowed origins should be accepted, while requests from other origins should be rejected.

**Validates: Requirements 4.4**

### Property 7: Error Response Transformation

*For any* error that occurs (Gemini API errors, validation errors, or internal errors), the FastAPI Backend should return a structured error response with an appropriate HTTP status code and user-friendly error message.

**Validates: Requirements 1.5, 6.1, 6.5**

### Property 8: Comprehensive Logging

*For any* request, error, or significant event (startup, rate limit hit, API call), the FastAPI Backend should create log entries containing relevant metadata without exposing sensitive information like API keys.

**Validates: Requirements 7.1, 7.2, 7.3, 7.5**

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases:

**Backend Tests (Python with pytest):**
- Startup with missing API key returns error
- Startup with valid API key succeeds
- Rate limit resets after time window
- Timeout handling after configured period
- Course switching clears history in frontend
- Both servers run on correct ports
- AI requests route to FastAPI
- Non-AI requests route to Express
- Network failure displays error in UI
- Quota exceeded displays appropriate message
- Startup logs contain configuration info

**Frontend Tests (TypeScript with Vitest):**
- Error responses display as AI messages
- Rate limit error displays in chat
- Course selection clears conversation history

### Property-Based Testing

Property-based tests will verify universal properties across many inputs:

**Backend Property Tests (Python with Hypothesis):**
- Property 1: Request-Response Round Trip
- Property 2: Rate Limiting Enforcement  
- Property 3: Conversation History Management
- Property 4: Message Ordering Invariant
- Property 5: Request Validation
- Property 6: CORS Origin Enforcement
- Property 7: Error Response Transformation
- Property 8: Comprehensive Logging

**Testing Framework:**
- Backend: `pytest` + `hypothesis` for property-based testing
- Frontend: `vitest` for unit tests
- Minimum 100 iterations per property test

**Test Configuration:**
Each property-based test will be tagged with:
```python
# Feature: gemini-fastapi-integration, Property 1: Request-Response Round Trip
```

## Development Workflow

### Local Development Setup

1. **FastAPI Backend:**
   ```bash
   cd python-backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

2. **Express + React Frontend:**
   ```bash
   pnpm dev  # Runs on port 8080
   ```

3. **Environment Variables:**
   ```
   # python-backend/.env
   GEMINI_API_KEY=your_api_key_here
   RATE_LIMIT_REQUESTS=15
   RATE_LIMIT_WINDOW=60
   ALLOWED_ORIGINS=http://localhost:8080
   ```

### Development Mode Proxy

In development, the Express server (port 8080) will proxy `/api/chat` requests to FastAPI (port 8000) to avoid CORS issues.

**vite.config.ts update:**
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

### Production Deployment

**Option 1: Separate Services**
- Deploy FastAPI to a Python hosting service (e.g., Railway, Render)
- Deploy Express + React to Netlify/Vercel
- Configure frontend to call FastAPI production URL

**Option 2: Unified Deployment**
- Use Docker Compose to run both services
- Nginx reverse proxy to route requests

## Security Considerations

1. **API Key Protection:**
   - Never commit `.env` files
   - Use environment variables in production
   - Rotate keys periodically

2. **Rate Limiting:**
   - Prevents abuse of free tier API
   - IP-based limiting (consider user-based for production)

3. **Input Validation:**
   - Pydantic schemas validate all inputs
   - Max message length: 2000 characters
   - Max history: 10 messages

4. **CORS Configuration:**
   - Restrict to known frontend origins
   - No wildcard (*) in production

5. **Error Messages:**
   - User-friendly messages to frontend
   - Detailed errors only in logs
   - No sensitive data in responses

## Monitoring and Observability

### Metrics to Track

1. **Request Metrics:**
   - Total requests per minute
   - Success rate
   - Average response time
   - Rate limit hits

2. **Error Metrics:**
   - Error rate by type
   - Gemini API errors
   - Validation errors

3. **Usage Metrics:**
   - Messages per user
   - Conversation length distribution
   - Peak usage times

### Logging Strategy

**Log Levels:**
- INFO: Requests, responses, startup
- WARNING: Rate limits, retries
- ERROR: API failures, exceptions

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "endpoint": "/api/chat",
  "status": 200,
  "duration_ms": 1250,
  "ip": "192.168.1.1"
}
```

## Future Enhancements

1. **Streaming Responses:**
   - Implement Server-Sent Events (SSE)
   - Display tokens as they arrive
   - Better UX for long responses

2. **Material Context:**
   - Upload and process course materials
   - Include material content in prompts
   - Vector embeddings for relevant context retrieval

3. **Persistent Conversation History:**
   - Store conversations in database
   - Resume conversations across sessions
   - Export conversation history

4. **Advanced Rate Limiting:**
   - User-based limits (not just IP)
   - Different tiers (free vs premium)
   - Redis-backed rate limiting for distributed systems

5. **Analytics Dashboard:**
   - Real-time usage statistics
   - Error tracking
   - User engagement metrics
