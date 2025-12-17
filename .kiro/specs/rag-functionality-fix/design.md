# Design Document

## Overview

This design addresses critical failures in the existing RAG (Retrieval-Augmented Generation) system where uploaded PDFs are not being properly searched and chat history is not being integrated into AI responses. The system has the necessary infrastructure (material processing, vector search, context service) but is failing at key integration points, resulting in AI responses that cannot reference uploaded materials or maintain conversation continuity.

The fix focuses on strengthening the integration between components, adding comprehensive error handling, and ensuring reliable operation of the RAG pipeline from material upload through search and context integration.

## Architecture

### Current System Issues

```
Upload PDF → Processing Service → [FAILS] → No embeddings stored
Chat Message → Search Service → [FAILS] → No materials found
Chat Message → Context Service → [PARTIAL] → Missing chat history
AI Request → [INCOMPLETE CONTEXT] → Generic responses
```

### Fixed System Flow

```
Upload PDF → Health Check → Processing Service → OCR + Embeddings → Database
Chat Message → Context Service → Chat History + Material Search → Enhanced Prompt → AI
```

### Component Integration

```
┌─────────────────────────────────────────────────────────────┐
│                     Chat Router                             │
│  (python-backend/routers/chat.py)                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Enhanced save_chat_message()                       │  │
│  │  1. Verify course ownership                          │  │
│  │  2. Get user context (preferences, academic, history)│  │
│  │  3. Perform material search with error handling     │  │
│  │  4. Format enhanced prompt with all context         │  │
│  │  5. Call AI service with complete context           │  │
│  │  6. Save conversation to history                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Enhanced Context Service                       │
│  (python-backend/services/context_service.py)              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  get_user_context() - ENHANCED                       │  │
│  │  ├─ get_preferences() - existing                     │  │
│  │  ├─ get_academic_info() - existing                   │  │
│  │  ├─ get_chat_history() - FIXED                       │  │
│  │  └─ format_context_prompt() - ENHANCED               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           Enhanced Material Processing Service              │
│  (python-backend/services/material_processing_service.py)  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  search_materials() - FIXED                          │  │
│  │  ├─ Health check AI Brain service                    │  │
│  │  ├─ Generate query embedding with retry              │  │
│  │  ├─ Execute vector search with fallback              │  │
│  │  └─ Format results with error handling               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  process_material() - ENHANCED                       │  │
│  │  ├─ Verify AI Brain service availability             │  │
│  │  ├─ Extract text with comprehensive error handling   │  │
│  │  ├─ Generate embeddings with retry logic             │  │
│  │  └─ Store results with detailed status tracking      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  AI Brain Client                            │
│  (python-backend/services/ai_brain_client.py)              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Enhanced Error Handling & Retry Logic              │  │
│  │  ├─ Connection health checks                         │  │
│  │  ├─ Comprehensive retry strategies                   │  │
│  │  ├─ Detailed error logging                           │  │
│  │  └─ Graceful degradation                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Enhanced Chat Router

**File:** `python-backend/routers/chat.py`

**Key Changes:**
- Add comprehensive error handling for material search
- Enhance logging for debugging RAG operations
- Improve context integration and prompt formatting
- Add health checks before RAG operations

**Enhanced Interface:**

```python
@router.post("/courses/{course_id}/chat", status_code=status.HTTP_201_CREATED)
async def save_chat_message(
    course_id: str,
    request: Request,
    chat_request: ChatRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Enhanced course-specific chat with reliable RAG and history persistence.
    
    Improvements:
    - Comprehensive error handling for all RAG operations
    - Enhanced logging for debugging
    - Reliable material search with fallback
    - Improved context integration
    """
```

### 2. Enhanced Context Service

**File:** `python-backend/services/context_service.py`

**Key Changes:**
- Fix chat history retrieval and formatting
- Enhance prompt formatting with better structure
- Add error handling for context operations
- Improve logging for debugging

**Enhanced Methods:**

```python
async def get_chat_history(
    self, 
    course_id: str, 
    client: Client, 
    limit: int = 10
) -> List[Message]:
    """
    FIXED: Retrieve recent chat history with proper error handling.
    
    Improvements:
    - Better error handling and logging
    - Proper message ordering and limiting
    - Graceful degradation on failures
    """

def format_context_prompt(
    self,
    context: UserContext,
    user_message: str,
    material_context: Optional[str] = None
) -> str:
    """
    ENHANCED: Format comprehensive context prompt for AI.
    
    Improvements:
    - Better structure and separation of context types
    - Enhanced material formatting
    - Improved chat history presentation
    - Clear section headers for AI parsing
    """
```

### 3. Enhanced Material Processing Service

**File:** `python-backend/services/material_processing_service.py`

**Key Changes:**
- Add health checks before processing operations
- Enhance error handling and retry logic
- Improve logging for debugging
- Add verification of database functions

**Enhanced Methods:**

```python
async def search_materials(
    self,
    course_id: str,
    query: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    FIXED: Reliable semantic search with comprehensive error handling.
    
    Improvements:
    - Health check AI Brain service before search
    - Enhanced error handling and logging
    - Fallback mechanisms for search failures
    - Better result formatting and validation
    """

async def process_material(self, material_id: str):
    """
    ENHANCED: Reliable material processing with health checks.
    
    Improvements:
    - Verify AI Brain service availability
    - Enhanced error handling and retry logic
    - Comprehensive status tracking
    - Detailed logging for debugging
    """
```

### 4. Enhanced AI Brain Client

**File:** `python-backend/services/ai_brain_client.py`

**Key Changes:**
- Add connection verification methods
- Enhance retry logic and error handling
- Improve logging for debugging
- Add graceful degradation strategies

**New Methods:**

```python
async def verify_connection(self) -> bool:
    """
    Verify AI Brain service is accessible and responding properly.
    
    Returns:
        True if service is fully operational, False otherwise
    """

async def verify_embedding_service(self) -> bool:
    """
    Verify embedding service is working by testing with sample text.
    
    Returns:
        True if embedding generation works, False otherwise
    """
```

## Data Models

### Enhanced Error Tracking

```python
class RAGOperationResult(BaseModel):
    """Result of a RAG operation with detailed status."""
    success: bool
    operation: str  # "material_search", "chat_history", "context_format"
    data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: float
    timestamp: str

class RAGContext(BaseModel):
    """Complete RAG context with operation results."""
    user_context: UserContext
    material_search_result: RAGOperationResult
    chat_history_result: RAGOperationResult
    prompt_format_result: RAGOperationResult
    total_execution_time: float
```

### Enhanced Material Search Result

```python
class EnhancedMaterialSearchResult(BaseModel):
    """Enhanced search result with additional metadata."""
    material_id: str
    name: str
    excerpt: str
    similarity_score: float
    file_type: str
    processing_status: str  # For debugging
    processed_at: Optional[str]
    excerpt_length: int  # For prompt optimization
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all properties identified in the prework, here are the key redundancies to address:

- Properties 1.3, 2.2, 5.1, 5.2 all test prompt formatting - can be combined into comprehensive prompt structure properties
- Properties 3.1, 7.1, 7.2, 7.3 all test health checks - can be unified into component verification properties  
- Properties 4.1, 4.2, 4.3 all test search operations - can be combined into comprehensive search properties
- Properties 6.1, 6.2, 6.3, 6.4, 6.5 all test logging - can be unified into comprehensive logging properties

### Correctness Properties

Property 1: Material search triggers for course chats
*For any* chat message sent in a course with processed materials, the system should perform semantic search using the message as query
**Validates: Requirements 1.1**

Property 2: Search results are limited and ranked
*For any* material search with results, the system should return at most 3 results ranked by similarity score in descending order
**Validates: Requirements 1.2, 4.3**

Property 3: Chat history retrieval respects limits
*For any* course with chat history, retrieving history should return at most 10 messages in chronological order
**Validates: Requirements 2.1, 2.3**

Property 4: Prompt includes available context
*For any* chat request with retrieved materials and history, the AI prompt should include clearly separated sections for materials, history, and current question
**Validates: Requirements 1.3, 2.2, 5.1, 5.2, 5.3, 5.4**

Property 5: Processing verifies AI Brain availability
*For any* material processing operation, the system should verify AI Brain service health before attempting OCR or embedding generation
**Validates: Requirements 3.1, 7.1**

Property 6: Successful processing stores complete data
*For any* material that processes successfully, the database should contain extracted text, 1024-dimensional embedding, status 'completed', and processed_at timestamp
**Validates: Requirements 3.4**

Property 7: Search generates query embeddings
*For any* semantic search operation, the system should generate a query embedding before executing vector similarity search
**Validates: Requirements 4.1, 4.2**

Property 8: Search results include required metadata
*For any* search result, the response should include material_id, name, excerpt, similarity_score, and file_type
**Validates: Requirements 4.4**

Property 9: Error handling enables graceful degradation
*For any* RAG operation failure, the system should log detailed error information and continue with available context rather than failing the entire request
**Validates: Requirements 2.5, 4.5, 6.1, 6.2, 6.3, 8.4, 8.5**

Property 10: Component verification enables functionality
*For any* system startup, when all RAG components are verified as available, the system should enable full RAG functionality
**Validates: Requirements 7.5**

Property 11: Edge cases handled gracefully
*For any* chat request in courses without materials or with unprocessed materials, the system should proceed with available context (history only)
**Validates: Requirements 8.1, 8.2, 8.3**

Property 12: Processing failures update status correctly
*For any* material processing that fails, the status should be 'failed' with error_message containing diagnostic information
**Validates: Requirements 3.5**

Property 13: Logging captures operation details
*For any* RAG operation, the system should log operation type, parameters, execution time, and success/failure status
**Validates: Requirements 6.4, 6.5**

Property 14: Database function verification
*For any* search operation, the system should verify the vector search function exists before attempting to use it
**Validates: Requirements 7.2, 7.3**

Property 15: Service health checks work correctly
*For any* AI Brain service health check, the system should correctly identify service availability and log the result
**Validates: Requirements 7.4**

## Error Handling

### RAG Operation Failures

| Failure Scenario | Detection Method | Recovery Strategy | User Impact |
|------------------|------------------|-------------------|-------------|
| **AI Brain Service Down** | Health check timeout | Skip AI-dependent operations, log warning | Chat works without material search |
| **Embedding Generation Fails** | API error response | Log error, proceed without materials | Chat works with history only |
| **Vector Search Function Missing** | Database function check | Log error, disable search | Chat works without material context |
| **Chat History Query Fails** | Database exception | Log error, proceed with empty history | Chat works without conversation context |
| **Material Processing Fails** | OCR/embedding errors | Update status to 'failed', allow retry | Materials not searchable until retry |
| **Search Query Too Short** | Input validation | Skip search, log attempt | Chat works with history only |
| **Database Connection Lost** | Connection exception | Retry with exponential backoff | Temporary degradation, then recovery |

### Error Recovery Strategies

```python
class RAGErrorHandler:
    """Centralized error handling for RAG operations."""
    
    async def handle_search_failure(
        self, 
        error: Exception, 
        course_id: str, 
        query: str
    ) -> List[Dict]:
        """Handle material search failures gracefully."""
        logger.error(f"Material search failed for course {course_id}: {error}")
        # Return empty results to allow chat to continue
        return []
    
    async def handle_history_failure(
        self, 
        error: Exception, 
        course_id: str
    ) -> List[Message]:
        """Handle chat history retrieval failures gracefully."""
        logger.error(f"Chat history retrieval failed for course {course_id}: {error}")
        # Return empty history to allow chat to continue
        return []
    
    async def handle_processing_failure(
        self, 
        error: Exception, 
        material_id: str
    ):
        """Handle material processing failures with detailed logging."""
        logger.error(f"Material processing failed for {material_id}: {error}")
        # Update material status to failed with error details
        await self._update_material_status(material_id, "failed", str(error))
```

### Logging Strategy

```python
# RAG Operation Logging
logger.info(f"RAG operation started: {operation_type} for course {course_id}")
logger.info(f"Material search: {len(results)} results in {duration:.2f}s")
logger.info(f"Chat history: {len(history)} messages retrieved")
logger.info(f"Context prompt: {len(prompt)} characters generated")

# Error Logging
logger.error(f"RAG component failure: {component} - {error}", exc_info=True)
logger.warning(f"RAG degraded mode: {reason} - continuing with available context")

# Performance Logging
logger.info(f"RAG total time: {total_time:.2f}s (search: {search_time:.2f}s, history: {history_time:.2f}s)")
```

## Testing Strategy

### Unit Tests

**Test Coverage:**
1. Enhanced context service methods (chat history retrieval, prompt formatting)
2. Enhanced material search with error handling
3. AI Brain client health checks and error recovery
4. Error handling for all RAG operations
5. Prompt formatting with various context combinations

**Example Tests:**
```python
def test_chat_history_retrieval_with_limit():
    """Test chat history respects 10 message limit."""
    # Given: Course with 15 chat messages
    # When: get_chat_history() called
    # Then: Returns exactly 10 most recent messages in chronological order

def test_material_search_with_ai_brain_failure():
    """Test material search handles AI Brain service failures gracefully."""
    # Given: AI Brain service is down
    # When: search_materials() called
    # Then: Returns empty results and logs error without throwing exception

def test_prompt_formatting_with_complete_context():
    """Test prompt formatting includes all available context."""
    # Given: Materials, chat history, and user preferences available
    # When: format_context_prompt() called
    # Then: Prompt includes clearly separated sections for all context types

def test_processing_health_check_before_operations():
    """Test material processing verifies AI Brain service before starting."""
    # Given: AI Brain service health check
    # When: process_material() called
    # Then: Health check performed before OCR/embedding operations

def test_graceful_degradation_multiple_failures():
    """Test system continues working when multiple RAG components fail."""
    # Given: AI Brain down, database search function missing
    # When: Chat request sent
    # Then: Basic chat works with available context only
```

### Property-Based Tests

We'll use **pytest** with **hypothesis** for property-based testing in Python.

Each property-based test should run a minimum of 100 iterations to ensure coverage across random inputs.

Property tests will be tagged with comments referencing the design document:
- Format: `# Feature: rag-functionality-fix, Property {number}: {property_text}`

### Integration Tests

**Test Scenarios:**
1. End-to-end RAG flow: Upload PDF → Process → Chat with material reference
2. Chat history continuity: Multiple messages → Verify history in subsequent requests
3. Error recovery: Simulate AI Brain failure → Verify graceful degradation
4. Component health checks: System startup → Verify all components checked
5. Search functionality: Upload materials → Search → Verify results ranked correctly

### Manual Testing

**Test Cases:**
1. Upload PDF with known content → Ask question about content → Verify AI references material
2. Have conversation → Send follow-up → Verify AI remembers previous context
3. Stop AI Brain service → Send chat → Verify chat still works without materials
4. Upload corrupted file → Verify processing fails gracefully with clear error
5. Search with very short query → Verify system handles gracefully

## Implementation Notes

### Performance Considerations

1. **Parallel Operations:** Use `asyncio.gather()` to fetch context components simultaneously
2. **Health Check Caching:** Cache AI Brain service health status for 30 seconds
3. **Search Optimization:** Limit search to top 3 results to minimize latency
4. **Error Recovery:** Implement exponential backoff for transient failures
5. **Logging Efficiency:** Use structured logging for better performance monitoring

### Debugging Enhancements

```python
# Enhanced logging for RAG debugging
@contextmanager
async def rag_operation_context(operation: str, **kwargs):
    """Context manager for RAG operation logging."""
    start_time = time.time()
    logger.info(f"RAG {operation} started", extra=kwargs)
    try:
        yield
        duration = time.time() - start_time
        logger.info(f"RAG {operation} completed in {duration:.2f}s", extra=kwargs)
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"RAG {operation} failed after {duration:.2f}s: {e}", extra=kwargs)
        raise
```

### Configuration Enhancements

```python
# Enhanced configuration for RAG reliability
RAG_CONFIG = {
    "ai_brain_health_check_timeout": 5.0,
    "ai_brain_health_check_cache_ttl": 30.0,
    "material_search_timeout": 10.0,
    "chat_history_limit": 10,
    "search_result_limit": 3,
    "max_retry_attempts": 3,
    "retry_delay_seconds": 1.0,
    "retry_backoff_multiplier": 2.0,
    "enable_graceful_degradation": True,
    "log_rag_operations": True
}
```

## Dependencies

- **Existing:** All current dependencies remain unchanged
- **Enhanced:** Improved error handling in existing services
- **New:** Enhanced logging and monitoring capabilities
- **Database:** Manual Supabase update required to ensure vector embedding dimension is 1024 (user will handle this manually)

## Security Considerations

1. **Error Information:** Avoid exposing internal details in error responses to users
2. **Logging Security:** Ensure logs don't contain sensitive user data or API keys
3. **Access Control:** Maintain existing RLS policies for all database operations
4. **Service Communication:** Ensure AI Brain service communication remains local-only

## Deployment Notes

1. **Zero Downtime:** All changes are backward compatible
2. **Gradual Rollout:** Can be deployed incrementally (service by service)
3. **Monitoring:** Enhanced logging provides better operational visibility
4. **Rollback:** Easy rollback since no schema changes are required
5. **Health Checks:** New health checks provide better service monitoring