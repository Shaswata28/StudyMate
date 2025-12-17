# Implementation Plan

- [x] 1. Database schema migration




  - Create SQL migration to add new columns to materials table
  - Add extracted_text, embedding, processing_status, processed_at, error_message columns
  - Create indexes for processing_status and embedding (HNSW)
  - Provide SQL script for manual execution in Supabase
  - _Requirements: 1.1, 9.1, 9.2, 9.3, 9.4_

- [x] 2. Create AI Brain client





  - Create AIBrainClient class with methods for extract_text, generate_embedding, and health_check
  - Implement HTTP communication with AI Brain service endpoints (/router and /utility/embed)
  - Add timeout configuration (default 5 minutes for OCR processing)
  - Add error handling for connection failures and service unavailability
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2.1 Write property test for AI Brain OCR







  - **Property 4: OCR extracts text from files**
  - **Validates: Requirements 2.1, 2.2**

- [x] 2.2 Write property test for embedding generation







  - **Property 6: Embedding generation for extracted text**
  - **Validates: Requirements 3.1**

- [x] 3. Create material processing service








  - Create MaterialProcessingService class with process_material method
  - Implement text extraction workflow using AI Brain client
  - Implement embedding generation workflow using AI Brain client
  - Add status tracking (pending → processing → completed/failed)
  - Implement error handling and logging for processing failures
  - Add timeout handling for long-running operations
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.2, 3.4, 8.1, 8.2, 8.3, 8.4_

- [ ]* 3.1 Write property test for processing status transitions
  - **Property 2: Background processing is triggered**
  - **Validates: Requirements 1.2, 1.3**

- [ ]* 3.2 Write property test for successful processing
  - **Property 3: Successful processing stores data and updates status**
  - **Validates: Requirements 1.4, 1.5, 2.3, 3.2**

- [ ]* 3.3 Write property test for failed processing
  - **Property 5: Failed processing updates status with error**
  - **Validates: Requirements 2.4, 3.4, 8.3**

- [ ]* 3.4 Write property test for embedding dimensionality (1024 dimensions)
  - **Property 16: Embeddings have correct dimensionality**
  - **Validates: Requirements 9.2**

- [x] 4. Implement background task queue





  - Set up FastAPI BackgroundTasks for async processing
  - Create queue_material_processing function
  - Ensure upload endpoint returns immediately without blocking
  - _Requirements: 8.1_

- [ ]* 5.1 Write property test for async processing
  - **Property 13: Async processing doesn't block upload**
  - **Validates: Requirements 8.1**

- [x] 5. Update materials upload endpoint




  - Modify upload_material endpoint to set initial status as 'pending'
  - Queue background processing task after file upload
  - Return material metadata immediately with pending status
  - _Requirements: 1.1, 1.2_

- [ ]* 5.1 Write property test for upload workflow
  - **Property 1: Upload creates storage and database record**
  - **Validates: Requirements 1.1**

- [x] 6. Update material response schemas



  - Add processing_status, processed_at, error_message, has_embedding to MaterialResponse
  - Create MaterialSearchResult schema with material_id, name, excerpt, similarity_score, file_type
  - Create MaterialSearchRequest schema with query and limit fields
  - _Requirements: 6.1, 4.4_

- [ ]* 7.1 Write property test for status display
  - **Property 12: Status displayed in material details**
  - **Validates: Requirements 6.1**

- [x] 7. Implement semantic search functionality




  - Add search_materials method to MaterialProcessingService
  - Implement query embedding generation using AI Brain client
  - Implement vector similarity search using pgvector
  - Return results ranked by similarity score
  - Handle edge cases (empty course, no results)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 7.1 Write property test for search query embedding
  - **Property 7: Search query generates embedding**
  - **Validates: Requirements 4.1, 4.2**

- [ ]* 7.2 Write property test for search result ranking
  - **Property 8: Search results are ranked by relevance**
  - **Validates: Requirements 4.3**

- [ ]* 7.3 Write property test for search result completeness
  - **Property 9: Search results include metadata and scores**
  - **Validates: Requirements 4.4**

- [x] 8. Create semantic search API endpoint





  - Add GET /courses/{course_id}/materials/search endpoint
  - Validate course ownership
  - Call search_materials service method
  - Return ranked search results
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 9. Integrate RAG into chat endpoint





  - Modify chat endpoint to accept optional course_id parameter
  - Perform semantic search on course materials when course_id provided
  - Retrieve top 3 most relevant material excerpts
  - Include material context in AI prompt
  - Handle cases with no relevant materials
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ]* 9.1 Write property test for RAG material retrieval
  - **Property 10: RAG retrieves top 3 materials**
  - **Validates: Requirements 5.2**

- [ ]* 9.2 Write property test for context inclusion
  - **Property 11: Material context included in AI prompt**
  - **Validates: Requirements 5.3**

- [x] 10. Add error handling and logging





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

- [x] 11. Update existing material endpoints




  - Update list_materials to include new status fields
  - Update get_material to include new status fields
  - Ensure backward compatibility with existing clients
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12. Add configuration and environment setup





  - Add AI Brain service configuration to config.py
  - Add environment variable for AI_BRAIN_ENDPOINT (default: http://localhost:8001)
  - Add processing timeout configuration
  - Add startup health check for AI Brain service
  - Document all configuration options
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.4_

- [x] 13. Create documentation





  - Document SQL migration steps for Supabase
  - Document API endpoints (upload, search, chat with RAG)
  - Document configuration options
  - Document Phase 2 migration path
  - Create examples for semantic search and RAG usage
  - _Requirements: All_

- [x] 16. Final checkpoint - Ensure all tests pass




  - Ensure all tests pass, ask the user if questions arise.
