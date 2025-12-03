# Design Document

## Overview

This feature adds automatic OCR and vector embedding capabilities to the materials system. When users upload PDFs or images, the system extracts text content and generates semantic embeddings for intelligent retrieval during AI conversations. The design uses an abstract provider pattern to support both immediate Gemini API implementation (Phase 1) and future router-based multi-model architecture (Phase 2).

## Architecture

### High-Level Architecture

```
┌─────────────┐
│   Client    │
│  (Upload)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐  │
│  │  Materials Router                 │  │
│  │  - Upload endpoint                │  │
│  │  - Search endpoint                │  │
│  └────────┬──────────────────────────┘  │
│           │                              │
│           ▼                              │
│  ┌───────────────────────────────────┐  │
│  │  Background Processing Service    │  │
│  │  - Async task queue               │  │
│  │  - Process materials              │  │
│  └────────┬──────────────────────────┘  │
│           │                              │
│           ▼                              │
│  ┌───────────────────────────────────┐  │
│  │  AI Provider (Abstract Interface) │  │
│  │  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │   Gemini    │  │   Router    │ │  │
│  │  │  (Phase 1)  │  │  (Phase 2)  │ │  │
│  │  └─────────────┘  └─────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐    ┌──────────────┐
│   Supabase   │    │   Supabase   │
│   Storage    │    │  PostgreSQL  │
│   (Files)    │    │  (Metadata)  │
└──────────────┘    └──────────────┘
```

### Phase 1: Gemini Implementation

```
Upload → Store File → Create DB Record → Background Job
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  Gemini Service │
                                    │  - OCR          │
                                    │  - Embeddings   │
                                    └─────────────────┘
                                              │
                                              ▼
                                    Update DB with results
```

### Phase 2: Router Architecture (Future)

```
Upload → Store File → Create DB Record → Background Job
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │ Router Service  │
                                    │ (Orchestrator)  │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
            ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
            │  DeepSeek    │        │  Llama 3.2   │        │ Qwen Coder   │
            │  (OCR)       │        │  (Chat)      │        │ (Code)       │
            │ Google Colab │        │ Google Colab │        │ Google Colab │
            └──────────────┘        └──────────────┘        └──────────────┘
                    │
                    ▼
          Update DB with results
```

## Components and Interfaces

### 1. Database Schema Extension

**Materials Table Additions:**
```sql
-- New columns to add to existing materials table
ALTER TABLE materials ADD COLUMN extracted_text TEXT;
ALTER TABLE materials ADD COLUMN embedding VECTOR(384);
ALTER TABLE materials ADD COLUMN processing_status TEXT DEFAULT 'pending' 
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));
ALTER TABLE materials ADD COLUMN processed_at TIMESTAMPTZ;
ALTER TABLE materials ADD COLUMN error_message TEXT;

-- Indexes for performance
CREATE INDEX idx_materials_processing_status ON materials(processing_status);
CREATE INDEX idx_materials_embedding ON materials USING hnsw (embedding vector_cosine_ops);
```

### 2. AI Provider Interface (Abstract)

```python
from abc import ABC, abstractmethod
from typing import Optional

class AIProvider(ABC):
    """Abstract interface for AI providers (Gemini, Router, etc.)"""
    
    @abstractmethod
    async def extract_text(self, file_data: bytes, mime_type: str) -> str:
        """Extract text from file using OCR"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate vector embedding from text"""
        pass
    
    @abstractmethod
    async def chat_with_context(
        self, 
        message: str, 
        context: list[str],
        history: Optional[list] = None
    ) -> str:
        """Generate chat response with material context"""
        pass
```

### 3. Gemini Provider Implementation (Phase 1)

```python
class GeminiProvider(AIProvider):
    """Gemini API implementation of AI provider"""
    
    def __init__(self, api_key: str):
        self.client = genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def extract_text(self, file_data: bytes, mime_type: str) -> str:
        """Use Gemini vision/PDF capabilities for OCR"""
        # Implementation using Gemini API
        pass
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Use Gemini embedding model"""
        # Implementation using Gemini embedding API
        pass
    
    async def chat_with_context(
        self, 
        message: str, 
        context: list[str],
        history: Optional[list] = None
    ) -> str:
        """Generate response with material context"""
        # Implementation using Gemini chat API
        pass
```

### 4. Router Provider Implementation (Phase 2 - Future)

```python
class RouterProvider(AIProvider):
    """Router-based multi-model implementation"""
    
    def __init__(self, router_endpoint: str, api_key: str):
        self.router_endpoint = router_endpoint
        self.api_key = api_key
    
    async def extract_text(self, file_data: bytes, mime_type: str) -> str:
        """Route to DeepSeek OCR model in Colab"""
        # POST to router_endpoint/ocr with task routing
        pass
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Route to embedding model"""
        # POST to router_endpoint/embed with task routing
        pass
    
    async def chat_with_context(
        self, 
        message: str, 
        context: list[str],
        history: Optional[list] = None
    ) -> str:
        """Route to Llama 3.2 or Qwen Coder based on query type"""
        # Router determines if it's code-related → Qwen Coder
        # Otherwise → Llama 3.2
        pass
```

### 5. Material Processing Service

```python
class MaterialProcessingService:
    """Handles background processing of uploaded materials"""
    
    def __init__(self, ai_provider: AIProvider, supabase_client):
        self.ai_provider = ai_provider
        self.supabase = supabase_client
    
    async def process_material(self, material_id: str):
        """
        Process a material: extract text and generate embedding
        """
        # 1. Update status to 'processing'
        # 2. Download file from storage
        # 3. Extract text using AI provider
        # 4. Generate embedding using AI provider
        # 5. Update database with results
        # 6. Update status to 'completed' or 'failed'
        pass
    
    async def search_materials(
        self, 
        course_id: str, 
        query: str, 
        limit: int = 3
    ) -> list[dict]:
        """
        Semantic search for materials
        """
        # 1. Generate embedding for query
        # 2. Perform vector similarity search
        # 3. Return top results with scores
        pass
```

### 6. Background Task Queue

```python
from fastapi import BackgroundTasks

async def queue_material_processing(
    material_id: str,
    background_tasks: BackgroundTasks
):
    """Queue material for background processing"""
    background_tasks.add_task(
        processing_service.process_material,
        material_id
    )
```

### 7. Updated Materials Router

```python
@router.post("/courses/{course_id}/materials")
async def upload_material(
    course_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user: AuthUser = Depends(get_current_user)
):
    """Upload material and queue for processing"""
    # 1. Validate and upload file
    # 2. Create database record with status='pending'
    # 3. Queue background processing
    # 4. Return immediately with material metadata
    pass

@router.get("/courses/{course_id}/materials/search")
async def search_materials(
    course_id: str,
    query: str,
    limit: int = 3,
    user: AuthUser = Depends(get_current_user)
):
    """Semantic search across course materials"""
    # 1. Verify course ownership
    # 2. Perform semantic search
    # 3. Return ranked results
    pass
```

### 8. Enhanced Chat Router

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    course_id: Optional[str] = None,
    user: AuthUser = Depends(get_current_user)
):
    """Chat with RAG support"""
    # 1. If course_id provided, search materials
    # 2. Retrieve top 3 relevant material excerpts
    # 3. Include material context in AI prompt
    # 4. Generate and return response
    pass
```

## Data Models

### Updated MaterialResponse Schema

```python
class MaterialResponse(BaseModel):
    id: str
    course_id: str
    name: str
    file_path: str
    file_type: str
    file_size: int
    processing_status: Literal["pending", "processing", "completed", "failed"]
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    has_embedding: bool  # Computed: embedding IS NOT NULL
    created_at: str
    updated_at: str
```

### Material Search Result Schema

```python
class MaterialSearchResult(BaseModel):
    material_id: str
    name: str
    excerpt: str  # Relevant text excerpt
    similarity_score: float  # 0-1, higher is more relevant
    file_type: str
```

### Material Search Request Schema

```python
class MaterialSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=3, ge=1, le=10)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

1.1 WHEN a user uploads a material file THEN the System SHALL store the file in Supabase Storage and create a database record
  Thoughts: This is about the upload process working correctly for any valid file. We can test this by generating random valid files and ensuring they're stored and recorded.
  Testable: yes - property

1.2 WHEN a material is uploaded THEN the System SHALL initiate background processing to extract text and generate embeddings
  Thoughts: This is about ensuring background processing is triggered for all uploads. We can verify the processing status changes from 'pending'.
  Testable: yes - property

1.3 WHEN processing begins THEN the System SHALL update the material status to 'processing'
  Thoughts: This is a state transition that should happen for all materials. We can test by checking status after processing starts.
  Testable: yes - property

1.4 WHEN processing completes successfully THEN the System SHALL store extracted text and embeddings in the materials table
  Thoughts: This is about data persistence after successful processing. We can verify the database contains the expected data.
  Testable: yes - property

1.5 WHEN processing completes THEN the System SHALL update the material status to 'completed' and record the processed timestamp
  Thoughts: This is a state transition with timestamp recording. We can verify both status and timestamp are set.
  Testable: yes - property

2.1 WHEN a PDF material is processed THEN the System SHALL extract all text content using OCR capabilities
  Thoughts: This is about OCR working on PDFs. We can test with known PDFs and verify extracted text matches expected content.
  Testable: yes - property

2.2 WHEN an image material is processed THEN the System SHALL extract visible text using OCR capabilities
  Thoughts: This is about OCR working on images. We can test with images containing known text.
  Testable: yes - property

2.3 WHEN text extraction succeeds THEN the System SHALL store the extracted text in the materials table
  Thoughts: This is about data persistence after extraction. We can verify the database contains extracted text.
  Testable: yes - property

2.4 WHEN text extraction fails THEN the System SHALL update the material status to 'failed' and log the error
  Thoughts: This is about error handling. We can test with corrupted files and verify status and error logging.
  Testable: yes - property

2.5 WHEN a material contains no extractable text THEN the System SHALL store an empty string and mark status as 'completed'
  Thoughts: This is an edge case for empty content. We can test with blank images/PDFs.
  Testable: edge-case

3.1 WHEN text is extracted from a material THEN the System SHALL generate a vector embedding representing the semantic meaning
  Thoughts: This is about embedding generation for all extracted text. We can verify embeddings are created.
  Testable: yes - property

3.2 WHEN an embedding is generated THEN the System SHALL store it as a VECTOR(384) in the materials table
  Thoughts: This is about correct data type and storage. We can verify the embedding column contains 384-dimensional vectors.
  Testable: yes - property

3.3 WHEN embedding generation succeeds THEN the System SHALL ensure the embedding is indexed for fast similarity search
  Thoughts: This is about database indexing, which is a schema concern rather than runtime behavior.
  Testable: no

3.4 WHEN embedding generation fails THEN the System SHALL update the material status to 'failed' and log the error
  Thoughts: This is about error handling for embedding failures. We can test with invalid inputs.
  Testable: yes - property

3.5 WHEN a material has no text content THEN the System SHALL skip embedding generation and mark status as 'completed'
  Thoughts: This is an edge case for empty content. Related to 2.5.
  Testable: edge-case

4.1 WHEN a user submits a semantic search query THEN the System SHALL generate an embedding for the query text
  Thoughts: This is about query processing. We can verify embeddings are generated for search queries.
  Testable: yes - property

4.2 WHEN a query embedding is generated THEN the System SHALL perform vector similarity search against material embeddings
  Thoughts: This is about the search mechanism working. We can verify search is executed.
  Testable: yes - property

4.3 WHEN similarity search executes THEN the System SHALL return materials ranked by semantic relevance
  Thoughts: This is about result ordering. We can verify results are sorted by similarity score in descending order.
  Testable: yes - property

4.4 WHEN returning search results THEN the System SHALL include material metadata and relevance scores
  Thoughts: This is about response completeness. We can verify all required fields are present.
  Testable: yes - property

4.5 WHEN a course has no processed materials THEN the System SHALL return an empty result set
  Thoughts: This is an edge case for empty courses.
  Testable: edge-case

5.1 WHEN a user sends a chat message THEN the System SHALL perform semantic search on course materials using the message as query
  Thoughts: This is about RAG integration. We can verify search is triggered for chat messages.
  Testable: yes - property

5.2 WHEN relevant materials are found THEN the System SHALL retrieve the top 3 most relevant material excerpts
  Thoughts: This is about limiting results. We can verify exactly 3 or fewer results are retrieved.
  Testable: yes - property

5.3 WHEN materials are retrieved THEN the System SHALL include them as context in the AI prompt
  Thoughts: This is about prompt construction. We can verify the prompt contains material context.
  Testable: yes - property

5.4 WHEN the AI generates a response THEN the System SHALL ensure the response references the provided material context
  Thoughts: This is about AI behavior, which is non-deterministic and hard to test programmatically.
  Testable: no

5.5 WHEN no relevant materials are found THEN the System SHALL proceed with the chat request without material context
  Thoughts: This is an edge case for no matches.
  Testable: edge-case

6.1 WHEN a user views material details THEN the System SHALL display the current processing status
  Thoughts: This is about API response completeness. We can verify status is included in responses.
  Testable: yes - property

6.2 WHEN a material is pending processing THEN the System SHALL display status as 'pending'
  Thoughts: This is about correct status reporting. We can verify status matches database state.
  Testable: yes - example

6.3 WHEN a material is being processed THEN the System SHALL display status as 'processing'
  Thoughts: This is about correct status reporting during processing.
  Testable: yes - example

6.4 WHEN processing completes successfully THEN the System SHALL display status as 'completed' with timestamp
  Thoughts: This is about correct status reporting after completion.
  Testable: yes - example

6.5 WHEN processing fails THEN the System SHALL display status as 'failed' with error information
  Thoughts: This is about correct error status reporting.
  Testable: yes - example

7.1 WHEN implementing OCR services THEN the System SHALL use an abstract interface that supports multiple providers
  Thoughts: This is about code architecture, not runtime behavior.
  Testable: no

7.2 WHEN implementing embedding services THEN the System SHALL use an abstract interface that supports multiple providers
  Thoughts: This is about code architecture, not runtime behavior.
  Testable: no

7.3 WHEN switching AI providers THEN the System SHALL require only configuration changes and provider implementation
  Thoughts: This is about system design flexibility, not a testable property.
  Testable: no

7.4 WHEN using Gemini API THEN the System SHALL implement the provider interface for Gemini services
  Thoughts: This is about implementation compliance with interface.
  Testable: yes - example

7.5 WHERE router architecture is deployed THEN the System SHALL support provider implementation for router endpoints
  Thoughts: This is a future requirement about extensibility.
  Testable: no

8.1 WHEN material processing is initiated THEN the System SHALL execute processing asynchronously without blocking the upload response
  Thoughts: This is about async behavior. We can verify upload returns before processing completes.
  Testable: yes - property

8.2 WHEN processing encounters an error THEN the System SHALL log detailed error information for debugging
  Thoughts: This is about logging behavior. We can verify logs contain error details.
  Testable: yes - property

8.3 WHEN processing fails THEN the System SHALL update the material status to 'failed' with error details
  Thoughts: This is about error state management. We can verify status and error_message are set.
  Testable: yes - property

8.4 WHEN processing times out THEN the System SHALL mark the material as 'failed' and allow retry
  Thoughts: This is about timeout handling. We can test with long-running operations.
  Testable: yes - property

8.5 WHEN the system restarts THEN the System SHALL resume processing of materials in 'pending' or 'processing' status
  Thoughts: This is about recovery behavior after restart. Difficult to test in unit tests.
  Testable: no

9.1 WHEN the materials table is created THEN the System SHALL include columns for extracted_text, embedding, processing_status, and processed_at
  Thoughts: This is about schema definition, verified by migration scripts.
  Testable: no

9.2 WHEN embeddings are stored THEN the System SHALL use the VECTOR(384) data type for efficient storage
  Thoughts: This is about data type correctness. We can verify stored embeddings have 384 dimensions.
  Testable: yes - property

9.3 WHEN the materials table is indexed THEN the System SHALL create an HNSW index on the embedding column for fast similarity search
  Thoughts: This is about database indexing, which is a schema concern.
  Testable: no

9.4 WHEN querying by status THEN the System SHALL have an index on processing_status for efficient filtering
  Thoughts: This is about database indexing, which is a schema concern.
  Testable: no

9.5 WHEN querying by course THEN the System SHALL maintain the existing index on course_id for efficient lookups
  Thoughts: This is about database indexing, which is a schema concern.
  Testable: no

### Property Reflection

After reviewing all properties, here are the redundancies to address:

- Properties 2.4 and 3.4 both test error handling with status updates - can be combined into a general error handling property
- Properties 2.5 and 3.5 both handle empty content edge cases - these are the same scenario
- Properties 6.2, 6.3, 6.4, 6.5 are all examples of the same property (6.1) - status display correctness
- Properties 1.3, 1.5, 2.4, 8.3 all test status transitions - can be unified into a state machine property

### Correctness Properties

Property 1: Upload creates storage and database record
*For any* valid material file, uploading it should result in both a file stored in Supabase Storage and a corresponding database record with status 'pending'
**Validates: Requirements 1.1**

Property 2: Background processing is triggered
*For any* uploaded material, the system should initiate background processing that transitions the status from 'pending' to 'processing'
**Validates: Requirements 1.2, 1.3**

Property 3: Successful processing stores data and updates status
*For any* material that processes successfully, the database should contain extracted text, a 384-dimensional embedding, status 'completed', and a processed_at timestamp
**Validates: Requirements 1.4, 1.5, 2.3, 3.2**

Property 4: OCR extracts text from files
*For any* PDF or image material containing text, the OCR process should extract text content that can be stored in the database
**Validates: Requirements 2.1, 2.2**

Property 5: Failed processing updates status with error
*For any* material where processing fails, the status should be 'failed' and error_message should contain diagnostic information
**Validates: Requirements 2.4, 3.4, 8.3**

Property 6: Embedding generation for extracted text
*For any* material with non-empty extracted text, the system should generate a vector embedding
**Validates: Requirements 3.1**

Property 7: Search query generates embedding
*For any* semantic search query, the system should generate a query embedding before performing similarity search
**Validates: Requirements 4.1, 4.2**

Property 8: Search results are ranked by relevance
*For any* semantic search with results, the returned materials should be ordered by similarity score in descending order
**Validates: Requirements 4.3**

Property 9: Search results include metadata and scores
*For any* search result, the response should include material_id, name, excerpt, similarity_score, and file_type
**Validates: Requirements 4.4**

Property 10: RAG retrieves top 3 materials
*For any* chat message with a course context, the system should retrieve at most 3 most relevant material excerpts
**Validates: Requirements 5.2**

Property 11: Material context included in AI prompt
*For any* chat request with retrieved materials, the AI prompt should include the material excerpts as context
**Validates: Requirements 5.3**

Property 12: Status displayed in material details
*For any* material, the API response should include the current processing_status field
**Validates: Requirements 6.1**

Property 13: Async processing doesn't block upload
*For any* material upload, the HTTP response should return before background processing completes
**Validates: Requirements 8.1**

Property 14: Processing errors are logged
*For any* processing error, the system should write detailed error information to application logs
**Validates: Requirements 8.2**

Property 15: Processing timeout marks as failed
*For any* material processing that exceeds timeout threshold, the status should be marked as 'failed'
**Validates: Requirements 8.4**

Property 16: Embeddings have correct dimensionality
*For any* stored embedding, it should have exactly 384 dimensions
**Validates: Requirements 9.2**

## Error Handling

### Processing Errors

1. **OCR Failures**: Mark status as 'failed', store error message, log details
2. **Embedding Failures**: Mark status as 'failed', store error message, log details
3. **Timeout**: Mark status as 'failed' after configurable timeout (default: 5 minutes)
4. **Storage Errors**: Retry up to 3 times, then mark as 'failed'
5. **API Rate Limits**: Implement exponential backoff, queue for retry

### Search Errors

1. **Empty Query**: Return 400 Bad Request
2. **Invalid Course**: Return 404 Not Found
3. **Embedding Generation Failure**: Return 500 Internal Server Error with message
4. **Database Errors**: Return 500 Internal Server Error, log details

### Provider Errors

1. **Provider Unavailable**: Log error, mark material as 'failed', allow retry
2. **Authentication Failure**: Log error, return 500, alert administrators
3. **Invalid Response**: Log error, mark material as 'failed'

## Testing Strategy

### Unit Tests

1. **Provider Interface Tests**: Verify Gemini provider implements all interface methods
2. **Schema Validation Tests**: Verify MaterialResponse includes all new fields
3. **Status Transition Tests**: Verify correct status transitions (pending → processing → completed/failed)
4. **Error Handling Tests**: Verify errors are caught and logged appropriately
5. **Search Ranking Tests**: Verify results are sorted by similarity score

### Property-Based Tests

We'll use **pytest** with **hypothesis** for property-based testing in Python.

Each property-based test should run a minimum of 100 iterations to ensure coverage across random inputs.

Property tests will be tagged with comments referencing the design document:
- Format: `# Feature: material-ocr-embedding, Property {number}: {property_text}`
- Example: `# Feature: material-ocr-embedding, Property 1: Upload creates storage and database record`

### Integration Tests

1. **End-to-End Upload Test**: Upload file → verify storage → verify DB record → verify processing
2. **OCR Integration Test**: Upload PDF with known text → verify extracted text matches
3. **Embedding Integration Test**: Process material → verify embedding is generated and stored
4. **Search Integration Test**: Upload materials → search → verify relevant results returned
5. **RAG Integration Test**: Upload materials → chat with course context → verify materials retrieved

### Phase 2 Testing (Future)

1. **Router Integration Tests**: Verify router correctly routes to specialized models
2. **Model Switching Tests**: Verify switching providers doesn't break functionality
3. **Colab Connectivity Tests**: Verify connection to Google Colab endpoints
4. **Multi-Model Tests**: Verify DeepSeek OCR, Llama chat, Qwen code queries work correctly

## Configuration

### Environment Variables

```bash
# Phase 1: Gemini
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=models/embedding-001

# Phase 2: Router (Future)
AI_PROVIDER=router
ROUTER_ENDPOINT=https://your-colab-endpoint.com
ROUTER_API_KEY=your_router_key

# Processing Configuration
MATERIAL_PROCESSING_TIMEOUT=300  # 5 minutes
MAX_EMBEDDING_DIMENSION=384
SEARCH_RESULT_LIMIT=3
```

### Provider Selection

```python
def get_ai_provider() -> AIProvider:
    """Factory function to get configured AI provider"""
    provider_type = config.AI_PROVIDER
    
    if provider_type == "gemini":
        return GeminiProvider(api_key=config.GEMINI_API_KEY)
    elif provider_type == "router":
        return RouterProvider(
            router_endpoint=config.ROUTER_ENDPOINT,
            api_key=config.ROUTER_API_KEY
        )
    else:
        raise ValueError(f"Unknown provider: {provider_type}")
```

## Phase 2 Implementation Notes (Future)

### Router Architecture Details

The router service will run in Google Colab and handle:

1. **Request Classification**: Determine which model to use based on request type
2. **Model Loading**: Load models from Google Drive on-demand
3. **Request Routing**: Forward requests to appropriate model
4. **Response Aggregation**: Collect and format responses

### Model Specifications

- **DeepSeek OCR**: Specialized for document and image text extraction
- **Llama 3.2**: General-purpose chat and question answering
- **Qwen Coder 2.5**: Code generation, debugging, and technical queries

### Router Endpoint Design

```
POST /router/process
{
  "task_type": "ocr" | "chat" | "code",
  "data": {...},
  "context": {...}
}

Response:
{
  "model_used": "deepseek" | "llama" | "qwen",
  "result": {...},
  "processing_time": 1.23
}
```

### Migration Path

1. Implement and test with Gemini (Phase 1)
2. Deploy router service in Google Colab
3. Implement RouterProvider class
4. Update configuration to use router
5. Test thoroughly with both providers
6. Switch production to router
7. Monitor performance and adjust as needed

## Performance Considerations

1. **Async Processing**: All OCR and embedding generation happens in background
2. **Vector Indexing**: HNSW index provides fast approximate nearest neighbor search
3. **Result Limiting**: Search returns maximum 3 results to minimize latency
4. **Caching**: Consider caching embeddings for frequently searched queries
5. **Batch Processing**: Process multiple materials in parallel when possible

## Security Considerations

1. **File Validation**: Verify file types and sizes before processing
2. **Access Control**: Verify course ownership before processing or searching
3. **API Key Security**: Store provider API keys in environment variables
4. **Rate Limiting**: Implement rate limits on search endpoints
5. **Error Messages**: Don't expose internal details in error responses
