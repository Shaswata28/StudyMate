# Implementation Plan

- [x] 1. Database schema migration




  - Create SQL migration to add new columns to materials table
  - Add extracted_text, embedding, processing_status, processed_at, error_message columns
  - Create indexes for processing_status and embedding (HNSW)
  - Provide SQL script for manual execution in Supabase
  - _Requirements: 1.1, 9.1, 9.2, 9.3, 9.4_

- [ ] 2. Create AI provider abstraction layer
  - Define abstract AIProvider interface with extract_text, generate_embedding, and chat_with_context methods
  - Create provider factory function for selecting provider based on configuration
  - Add configuration variables for AI_PROVIDER, provider endpoints, and API keys
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 3. Implement Gemini provider (Phase 1)
  - Create GeminiProvider class implementing AIProvider interface
  - Implement extract_text method using Gemini vision/PDF capabilities
  - Implement generate_embedding method using Gemini embedding API
  - Implement chat_with_context method for RAG-enabled chat
  - Add error handling for Gemini API failures
  - _Requirements: 2.1, 2.2, 3.1, 5.4, 7.4_

- [ ]* 3.1 Write property test for Gemini OCR
  - **Property 4: OCR extracts text from files**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 3.2 Write property test for embedding generation
  - **Property 6: Embedding generation for extracted text**
  - **Validates: Requirements 3.1**

- [ ] 4. Create material processing service
  - Create MaterialProcessingService class with process_material method
  - Implement text extraction workflow using AI provider
  - Implement embedding generation workflow using AI provider
  - Add status tracking (pending → processing → completed/failed)
  - Implement error handling and logging for processing failures
  - Add timeout handling for long-running operations
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.2, 3.4, 8.1, 8.2, 8.3, 8.4_

- [ ]* 4.1 Write property test for processing status transitions
  - **Property 2: Background processing is triggered**
  - **Validates: Requirements 1.2, 1.3**

- [ ]* 4.2 Write property test for successful processing
  - **Property 3: Successful processing stores data and updates status**
  - **Validates: Requirements 1.4, 1.5, 2.3, 3.2**

- [ ]* 4.3 Write property test for failed processing
  - **Property 5: Failed processing updates status with error**
  - **Validates: Requirements 2.4, 3.4, 8.3**

- [ ]* 4.4 Write property test for embedding dimensionality
  - **Property 16: Embeddings have correct dimensionality**
  - **Validates: Requirements 9.2**

- [ ] 5. Implement background task queue
  - Set up FastAPI BackgroundTasks for async processing
  - Create queue_material_processing function
  - Ensure upload endpoint returns immediately without blocking
  - _Requirements: 8.1_

- [ ]* 5.1 Write property test for async processing
  - **Property 13: Async processing doesn't block upload**
  - **Validates: Requirements 8.1**

- [ ] 6. Update materials upload endpoint
  - Modify upload_material endpoint to set initial status as 'pending'
  - Queue background processing task after file upload
  - Return material metadata immediately with pending status
  - _Requirements: 1.1, 1.2_

- [ ]* 6.1 Write property test for upload workflow
  - **Property 1: Upload creates storage and database record**
  - **Validates: Requirements 1.1**

- [ ] 7. Update material response schemas
  - Add processing_status, processed_at, error_message, has_embedding to MaterialResponse
  - Create MaterialSearchResult schema with material_id, name, excerpt, similarity_score, file_type
  - Create MaterialSearchRequest schema with query and limit fields
  - _Requirements: 6.1, 4.4_

- [ ]* 7.1 Write property test for status display
  - **Property 12: Status displayed in material details**
  - **Validates: Requirements 6.1**

- [ ] 8. Implement semantic search functionality
  - Add search_materials method to MaterialProcessingService
  - Implement query embedding generation
  - Implement vector similarity search using pgvector
  - Return results ranked by similarity score
  - Handle edge cases (empty course, no results)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 8.1 Write property test for search query embedding
  - **Property 7: Search query generates embedding**
  - **Validates: Requirements 4.1, 4.2**

- [ ]* 8.2 Write property test for search result ranking
  - **Property 8: Search results are ranked by relevance**
  - **Validates: Requirements 4.3**

- [ ]* 8.3 Write property test for search result completeness
  - **Property 9: Search results include metadata and scores**
  - **Validates: Requirements 4.4**

- [ ] 9. Create semantic search API endpoint
  - Add GET /courses/{course_id}/materials/search endpoint
  - Validate course ownership
  - Call search_materials service method
  - Return ranked search results
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 10. Integrate RAG into chat endpoint
  - Modify chat endpoint to accept optional course_id parameter
  - Perform semantic search on course materials when course_id provided
  - Retrieve top 3 most relevant material excerpts
  - Include material context in AI prompt
  - Handle cases with no relevant materials
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ]* 10.1 Write property test for RAG material retrieval
  - **Property 10: RAG retrieves top 3 materials**
  - **Validates: Requirements 5.2**

- [ ]* 10.2 Write property test for context inclusion
  - **Property 11: Material context included in AI prompt**
  - **Validates: Requirements 5.3**

- [ ] 11. Add error handling and logging
  - Implement comprehensive error handling for all processing steps
  - Add detailed logging for debugging (OCR failures, embedding failures, timeouts)
  - Ensure errors are captured in error_message field
  - Add retry logic for transient failures
  - _Requirements: 2.4, 3.4, 8.2, 8.3_

- [ ]* 11.1 Write property test for error logging
  - **Property 14: Processing errors are logged**
  - **Validates: Requirements 8.2**

- [ ]* 11.2 Write property test for timeout handling
  - **Property 15: Processing timeout marks as failed**
  - **Validates: Requirements 8.4**

- [ ] 12. Update existing material endpoints
  - Update list_materials to include new status fields
  - Update get_material to include new status fields
  - Ensure backward compatibility with existing clients
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 13. Create Phase 2 router provider stub (documentation only)
  - Create RouterProvider class skeleton with interface implementation
  - Add detailed comments explaining router architecture
  - Document endpoint structure for router service
  - Add configuration examples for Phase 2 deployment
  - Mark as future implementation (not functional yet)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 14. Add configuration and environment setup
  - Add AI provider configuration to config.py
  - Add environment variables for Gemini API keys
  - Add environment variables for router endpoints (Phase 2)
  - Add processing timeout configuration
  - Document all configuration options
  - _Requirements: 7.3, 7.4, 7.5_

- [ ] 15. Create documentation
  - Document SQL migration steps for Supabase
  - Document API endpoints (upload, search, chat with RAG)
  - Document configuration options
  - Document Phase 2 migration path
  - Create examples for semantic search and RAG usage
  - _Requirements: All_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
