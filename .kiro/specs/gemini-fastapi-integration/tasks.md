# Implementation Plan

- [x] 1. Set up Python FastAPI backend project structure





  - Create `python-backend/` directory with proper structure
  - Create `requirements.txt` with dependencies: fastapi, uvicorn, google-generativeai, slowapi, pydantic, python-dotenv, pytest, hypothesis
  - Create `.env.example` file with required environment variables
  - Create `main.py` as FastAPI application entry point
  - _Requirements: 4.1, 4.2_

- [x] 2. Implement configuration management





  - Create `config.py` to load environment variables
  - Implement validation for required variables (GEMINI_API_KEY)
  - Add configuration for rate limiting, CORS, and Gemini settings
  - Implement startup validation that fails if API key is missing
  - _Requirements: 4.1, 4.2_

- [ ]* 2.1 Write unit test for configuration validation
  - Test startup with missing API key fails
  - Test startup with valid API key succeeds
  - Test configuration loads correct values from environment
  - _Requirements: 4.1, 4.2_

- [x] 3. Implement Pydantic data models





  - Create `models/schemas.py` with Message, ChatRequest, ChatResponse, ErrorResponse models
  - Add validation rules (message length 1-2000 chars, max 10 history messages)
  - _Requirements: 4.3_

- [ ]* 3.1 Write property test for request validation
  - **Property 5: Request Validation**
  - **Validates: Requirements 4.3, 4.5**
  - Generate random valid and invalid payloads
  - Verify valid requests pass validation
  - Verify invalid requests return 422 with field details
  - _Requirements: 4.3, 4.5_

- [x] 4. Implement Gemini API service





  - Create `services/gemini_service.py`
  - Implement function to initialize Gemini client with API key
  - Implement function to format conversation history for Gemini API
  - Implement function to call Gemini API with message and history
  - Add error handling for Gemini API errors with user-friendly messages
  - Add timeout configuration (30 seconds)
  - _Requirements: 1.2, 1.3, 3.2, 6.1_

- [ ]* 4.1 Write property test for conversation history formatting
  - **Property 3: Conversation History Management**
  - **Validates: Requirements 3.1, 3.2, 3.3**
  - Generate random conversation histories of varying lengths
  - Verify history is correctly formatted for Gemini
  - Verify sliding window keeps only last 10 messages
  - _Requirements: 3.1, 3.2, 3.3_

- [ ]* 4.2 Write property test for error transformation
  - **Property 7: Error Response Transformation**
  - **Validates: Requirements 1.5, 6.1, 6.5**
  - Generate various error types (API errors, validation errors, internal errors)
  - Verify all errors return structured responses with appropriate status codes
  - Verify error messages are user-friendly
  - _Requirements: 1.5, 6.1, 6.5_

- [x] 5. Implement rate limiting middleware





  - Create `middleware/rate_limiter.py`
  - Implement rate limiter using slowapi (15 requests per 60 seconds per IP)
  - Configure rate limiter to return HTTP 429 with user-friendly message
  - Add rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 5.1 Write property test for rate limiting
  - **Property 2: Rate Limiting Enforcement**
  - **Validates: Requirements 2.2**
  - Send multiple requests from same IP
  - Verify requests are accepted until limit reached
  - Verify subsequent requests return 429 without calling Gemini
  - Verify requests work again after time window resets
  - _Requirements: 2.2_

- [ ]* 5.2 Write unit test for rate limit reset
  - Test that rate limit resets after configured time window
  - Verify requests succeed after reset
  - _Requirements: 2.5_

- [x] 6. Implement chat endpoint





  - Create `routers/chat.py`
  - Implement POST /api/chat endpoint
  - Validate request using ChatRequest schema
  - Call Gemini service with message and history
  - Return ChatResponse with AI response and timestamp
  - Handle all error types with appropriate status codes
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [ ]* 6.1 Write property test for request-response round trip
  - **Property 1: Request-Response Round Trip**
  - **Validates: Requirements 1.1, 1.2, 1.3**
  - Generate random valid messages
  - Mock Gemini API responses
  - Verify backend forwards request to Gemini and returns response correctly
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 6.2 Write unit test for timeout handling
  - Test that requests timeout after configured period
  - Verify appropriate error response is returned
  - _Requirements: 6.2_

- [x] 7. Implement logging throughout the backend





  - Add request logging middleware (timestamp, endpoint, IP, status, duration)
  - Add error logging with full details and stack traces
  - Add Gemini API call logging (without sensitive data)
  - Add startup logging with configuration status
  - Add rate limit event logging
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 7.1 Write property test for comprehensive logging
  - **Property 8: Comprehensive Logging**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.5**
  - Generate various requests, errors, and events
  - Verify logs are created for each event type
  - Verify logs contain required metadata
  - Verify logs do not contain sensitive data (API keys)
  - _Requirements: 7.1, 7.2, 7.3, 7.5_

- [ ]* 7.2 Write unit test for startup logging
  - Test that startup creates log entry with configuration info
  - _Requirements: 7.4_

- [x] 8. Configure CORS and wire up FastAPI application





  - In `main.py`, configure CORS middleware with allowed origins from environment
  - Register rate limiter middleware
  - Register logging middleware
  - Register chat router
  - Add health check endpoint GET /health
  - _Requirements: 4.4_

- [ ]* 8.1 Write property test for CORS enforcement
  - **Property 6: CORS Origin Enforcement**
  - **Validates: Requirements 4.4**
  - Generate requests from various origins
  - Verify only allowed origins are accepted
  - Verify other origins are rejected
  - _Requirements: 4.4_

- [x] 9. Checkpoint - Ensure all backend tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Update frontend to call FastAPI backend





  - Update `client/pages/Dashboard.tsx` handleSendMessage function
  - Change from mock response to fetch call to `/api/chat`
  - Include conversation history (last 10 messages) in request
  - Format history as array of {role, content} objects
  - Handle success response and add AI message to state
  - Handle error responses by displaying error as AI message
  - Maintain existing loading state behavior
  - _Requirements: 1.1, 1.4, 2.4, 3.1, 6.3, 6.4_

- [ ]* 10.1 Write unit test for error display
  - Test that error responses display as AI messages in chat
  - Test rate limit error displays correctly
  - Test network error displays correctly
  - _Requirements: 2.4, 6.3, 6.4_

- [ ]* 10.2 Write unit test for course switching
  - Test that selecting a new course clears conversation history
  - _Requirements: 3.4_

- [ ]* 10.3 Write property test for message ordering
  - **Property 4: Message Ordering Invariant**
  - **Validates: Requirements 3.5**
  - Generate random sequences of user and AI messages
  - Verify order and role attribution is preserved throughout
  - _Requirements: 3.5_

- [x] 11. Configure development proxy






  - Update `vite.config.ts` to proxy `/api/chat` requests to `http://localhost:8000`
  - Test that requests from frontend reach FastAPI backend in development
  - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 11.1 Write unit tests for routing
  - Test AI requests route to FastAPI
  - Test non-AI requests route to Express
  - Test both servers run on correct ports
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 12. Create development setup documentation





  - Create `python-backend/README.md` with setup instructions
  - Document environment variables in `.env.example`
  - Add instructions for running both servers locally
  - Document API endpoint specifications
  - _Requirements: 5.1_

- [ ] 13. Final checkpoint - End-to-end testing
  - Ensure all tests pass, ask the user if questions arise.
  - Start both FastAPI and Express servers
  - Test sending messages through the UI
  - Test rate limiting by sending multiple messages quickly
  - Test error handling by stopping FastAPI server
  - Verify conversation history is maintained
  - Verify course switching clears history
