# Implementation Plan

- [x] 1. Set up AI Brain service directory structure





  - Create ai-brain directory at project root
  - Create brain.py with the provided FastAPI implementation
  - Create requirements.txt with dependencies (fastapi, uvicorn, ollama, whisper, torch, httpx)
  - Create README.md with setup and usage instructions
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 2. Implement Brain Process Manager





  - Create python-backend/services/brain_manager.py
  - Implement BrainProcessManager class with subprocess management
  - Add start_brain() method to launch brain service as subprocess
  - Add stop_brain() method for graceful termination
  - Add is_healthy() method for health checks
  - Add restart_brain() method for recovery
  - _Requirements: 11.1, 11.3, 11.5_

- [x] 3. Implement Local AI Service





  - Create python-backend/services/local_ai_service.py
  - Implement LocalAIService class as Gemini replacement
  - Add generate_response() method for text/image/audio requests
  - Add generate_embedding() method for embedding requests
  - Add health_check() method
  - Handle multipart form data for attachments
  - Match gemini_service interface for drop-in replacement
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 4. Integrate brain manager with main backend startup





  - Modify python-backend/main.py to import brain_manager
  - Add startup event handler to start brain service
  - Add shutdown event handler to stop brain service
  - Implement health check waiting logic
  - Add error handling for brain startup failures
  - _Requirements: 11.1, 11.2, 11.3, 11.4_
-

- [x] 5. Update chat router to use local AI service




  - Modify python-backend/routers/chat.py
  - Replace gemini_service imports with local_ai_service
  - Update error handling for brain service errors
  - Maintain existing endpoint signatures
  - Update error codes and messages
  - Test all chat endpoints
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 6. Remove Gemini dependencies





  - Delete python-backend/services/gemini_service.py
  - Remove google-generativeai from requirements.txt
  - Remove GEMINI_API_KEY from .env and .env.example
  - Update any documentation referencing Gemini
  - Search codebase for remaining Gemini references
  - _Requirements: 7.5_

- [x] 7. Create installation and setup scripts





  - Create ai-brain/install.sh for dependency installation
  - Add Ollama installation check
  - Add model pulling verification (models already pulled)
  - Add Python dependency installation
  - Create startup verification script
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 8. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 9. Write integration tests for brain service
  - Test /router endpoint with text prompts
  - Test /router endpoint with image files
  - Test /router endpoint with audio files
  - Test /utility/embed endpoint
  - Test health check endpoint
  - Test error scenarios (invalid files, Ollama down)
  - _Requirements: 2.1, 3.1, 4.1, 5.1_

- [ ]* 10. Write unit tests for brain manager
  - Test subprocess startup and shutdown
  - Test health check logic
  - Test restart functionality
  - Mock subprocess for testing
  - Test error handling
  - _Requirements: 11.1, 11.3, 11.5_

- [ ]* 11. Write unit tests for local AI service
  - Test request formatting for text/image/audio
  - Test response parsing
  - Test error handling
  - Mock HTTP client
  - Test attachment handling
  - _Requirements: 7.1, 7.3_

- [ ]* 12. Write property test for text generation response structure
  - **Property 1: Text generation returns valid response structure**
  - **Validates: Requirements 2.3**
  - Generate random text prompts
  - Verify all responses contain "response" and "model" fields
  - Verify field types are correct

- [ ]* 13. Write property test for specialist model cleanup
  - **Property 6: Specialist model cleanup**
  - **Validates: Requirements 3.3, 5.3, 6.1**
  - Process multiple images and embeddings
  - Verify specialist models are unloaded after each request
  - Verify Qwen remains loaded

- [ ]* 14. Write property test for core model protection
  - **Property 13: Core model protection**
  - **Validates: Requirements 6.5**
  - Perform various cleanup operations
  - Verify Qwen 2.5 1.5B is never unloaded
  - Check model status after each cleanup

- [ ]* 15. Write property test for operation logging
  - **Property 16: Operation logging**
  - **Validates: Requirements 8.1, 8.2, 8.3**
  - Perform various operations (start, complete, fail)
  - Verify all operations are logged with correct details
  - Check log format and content

- [ ] 16. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
