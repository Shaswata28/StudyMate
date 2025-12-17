# Material OCR & Embedding Feature Guide

## Overview

This feature enables automatic OCR (Optical Character Recognition) and vector embedding generation for uploaded learning materials (PDFs, images). When users upload materials to a course, the system automatically extracts text content, generates semantic embeddings, and stores them for intelligent retrieval during AI conversations using Retrieval Augmented Generation (RAG).

### Key Capabilities

- **Automatic Text Extraction**: Extract text from PDFs and images using OCR
- **Semantic Embeddings**: Generate vector embeddings for semantic search
- **Background Processing**: Asynchronous processing without blocking uploads
- **Semantic Search**: Find materials based on meaning, not just keywords
- **RAG Integration**: AI automatically references relevant materials in responses
- **Status Tracking**: Monitor processing status of uploaded materials

### Architecture

The system uses a local AI Brain service (port 8001) that orchestrates specialized Ollama models:
- **qwen3-vl:2b**: Vision-language model for text extraction from images/PDFs
- **mxbai-embed-large**: Embedding model for semantic vector generation (384 dimensions)
- **Qwen 2.5**: Text generation model for chat responses

## Table of Contents

1. [Database Setup](#database-setup)
2. [Configuration](#configuration)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Processing Workflow](#processing-workflow)
6. [Error Handling](#error-handling)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Database Setup

### Prerequisites

- PostgreSQL database with pgvector extension enabled
- Supabase project (or self-hosted PostgreSQL with pgvector)

### Migration Steps

#### Step 1: Enable pgvector Extension

If not already enabled, run this in your Supabase SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Step 2: Run Migration

Execute the migration file `migrations/005_add_material_ocr_embedding.sql`:

```sql
-- Add new columns to materials table
ALTER TABLE materials 
ADD COLUMN extracted_text TEXT,
ADD COLUMN embedding VECTOR(384),
ADD COLUMN processing_status TEXT DEFAULT 'pending' 
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
ADD COLUMN processed_at TIMESTAMPTZ,
ADD COLUMN error_message TEXT;

-- Create index on processing_status for efficient filtering
CREATE INDEX idx_materials_processing_status ON materials(processing_status);

-- Create HNSW index on embedding column for fast vector similarity search
CREATE INDEX idx_materials_embedding ON materials USING hnsw (embedding vector_cosine_ops);
```

#### Step 3: Create Vector Search Function

Execute the migration file `migrations/006_add_vector_search_function.sql`:

```sql
CREATE OR REPLACE FUNCTION search_materials_by_embedding(
    p_course_id UUID,
    p_query_embedding VECTOR(384),
    p_limit INTEGER DEFAULT 3
)
RETURNS TABLE (
    material_id UUID,
    name TEXT,
    excerpt TEXT,
    similarity_score FLOAT,
    file_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id AS material_id,
        m.name,
        LEFT(m.extracted_text, 500) AS excerpt,
        1 - (m.embedding <=> p_query_embedding) AS similarity_score,
        m.file_type
    FROM materials m
    WHERE m.course_id = p_course_id
        AND m.embedding IS NOT NULL
        AND m.processing_status = 'completed'
    ORDER BY m.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

#### Verification

Verify the migration was successful:

```sql
-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'materials' 
AND column_name IN ('extracted_text', 'embedding', 'processing_status', 'processed_at', 'error_message');

-- Check indexes exist
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'materials' 
AND indexname IN ('idx_materials_processing_status', 'idx_materials_embedding');

-- Check function exists
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_name = 'search_materials_by_embedding';
```

---

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# AI Brain Service Configuration
AI_BRAIN_ENDPOINT=http://localhost:8001
AI_BRAIN_TIMEOUT=300  # 5 minutes for OCR processing

# Processing Configuration
MATERIAL_PROCESSING_TIMEOUT=300  # 5 minutes
SEARCH_RESULT_LIMIT=3

# Existing Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### AI Brain Service Setup

The backend requires the AI Brain service to be running on port 8001.

#### Start AI Brain Service

```bash
# Navigate to ai-brain directory
cd ai-brain

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the service
python brain.py
```

The AI Brain service will:
- Start on port 8001
- Load models on-demand (qwen3-vl:2b for OCR, mxbai-embed-large for embeddings)
- Automatically unload specialist models after use to free VRAM
- Keep the core text generation model (Qwen 2.5) persistent

#### Verify AI Brain Service

```bash
# Check service health
curl http://localhost:8001/

# Expected response: {"status": "ok"}
```

### Backend Configuration

The backend automatically checks AI Brain service availability on startup:

```python
# In main.py
@app.on_event("startup")
async def startup_event():
    """Verify AI Brain service is available"""
    is_healthy = await ai_brain_client.health_check()
    if not is_healthy:
        logger.warning(
            f"AI Brain service not available at {settings.AI_BRAIN_ENDPOINT}. "
            "Material processing will fail until service is started."
        )
    else:
        logger.info("AI Brain service connection verified")
```

---

## API Endpoints

### 1. Upload Material

Upload a file and queue it for processing.

**Endpoint**: `POST /api/courses/{course_id}/materials`

**Authentication**: Required (JWT token)

**Request**:
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: File to upload (PDF, JPG, PNG, GIF, WEBP)

**Response**: `201 Created`

```json
{
  "id": "uuid",
  "course_id": "uuid",
  "name": "document.pdf",
  "file_path": "user_id/course_id/document.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "processing_status": "pending",
  "processed_at": null,
  "error_message": null,
  "has_embedding": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Processing Status Values**:
- `pending`: Uploaded, waiting for processing
- `processing`: Currently extracting text and generating embedding
- `completed`: Successfully processed
- `failed`: Processing failed (see error_message)

**Example**:

```bash
curl -X POST "http://localhost:8000/api/courses/{course_id}/materials" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

### 2. List Materials

Get all materials for a course with processing status.

**Endpoint**: `GET /api/courses/{course_id}/materials`

**Authentication**: Required (JWT token)

**Response**: `200 OK`

```json
[
  {
    "id": "uuid",
    "course_id": "uuid",
    "name": "lecture-notes.pdf",
    "file_path": "user_id/course_id/lecture-notes.pdf",
    "file_type": "application/pdf",
    "file_size": 2048000,
    "processing_status": "completed",
    "processed_at": "2024-01-01T00:05:00Z",
    "error_message": null,
    "has_embedding": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:05:00Z"
  }
]
```

### 3. Get Material Details

Get metadata for a specific material.

**Endpoint**: `GET /api/materials/{material_id}`

**Authentication**: Required (JWT token)

**Response**: `200 OK`

```json
{
  "id": "uuid",
  "course_id": "uuid",
  "name": "textbook-chapter.pdf",
  "file_path": "user_id/course_id/textbook-chapter.pdf",
  "file_type": "application/pdf",
  "file_size": 5120000,
  "processing_status": "completed",
  "processed_at": "2024-01-01T00:10:00Z",
  "error_message": null,
  "has_embedding": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z"
}
```

### 4. Semantic Search

Search materials by semantic meaning.

**Endpoint**: `GET /api/courses/{course_id}/materials/search`

**Authentication**: Required (JWT token)

**Query Parameters**:
- `query` (required): Search query text
- `limit` (optional): Maximum results to return (1-10, default: 3)

**Response**: `200 OK`

```json
[
  {
    "material_id": "uuid",
    "name": "lecture-notes.pdf",
    "excerpt": "This chapter covers the fundamentals of machine learning...",
    "similarity_score": 0.87,
    "file_type": "application/pdf"
  },
  {
    "material_id": "uuid",
    "name": "textbook-chapter.pdf",
    "excerpt": "Neural networks are computational models inspired by...",
    "similarity_score": 0.82,
    "file_type": "application/pdf"
  }
]
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/courses/{course_id}/materials/search?query=machine%20learning%20basics&limit=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. Chat with RAG

Send a chat message with automatic material retrieval.

**Endpoint**: `POST /api/courses/{course_id}/chat`

**Authentication**: Required (JWT token)

**Request Body**:

```json
{
  "message": "What are the key concepts in machine learning?",
  "history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "model",
      "content": "Hi! How can I help you today?"
    }
  ],
  "attachments": []
}
```

**Response**: `201 Created`

```json
{
  "response": "Based on your course materials, the key concepts in machine learning include...",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**How RAG Works**:
1. System performs semantic search using your message as the query
2. Retrieves top 3 most relevant material excerpts
3. Includes material context in the AI prompt
4. AI generates response grounded in your course materials

**Example**:

```bash
curl -X POST "http://localhost:8000/api/courses/{course_id}/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain neural networks",
    "history": [],
    "attachments": []
  }'
```

### 6. Download Material

Download the original file.

**Endpoint**: `GET /api/materials/{material_id}/download`

**Authentication**: Required (JWT token)

**Response**: `200 OK` (file stream)

### 7. Delete Material

Delete a material and its file from storage.

**Endpoint**: `DELETE /api/materials/{material_id}`

**Authentication**: Required (JWT token)

**Response**: `200 OK`

```json
{
  "message": "Material deleted successfully"
}
```

---

## Usage Examples

### Example 1: Upload and Monitor Processing

```python
import requests
import time

# Upload material
response = requests.post(
    f"http://localhost:8000/api/courses/{course_id}/materials",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": open("lecture-notes.pdf", "rb")}
)

material = response.json()
material_id = material["id"]
print(f"Uploaded: {material['name']}, Status: {material['processing_status']}")

# Poll for completion
while True:
    response = requests.get(
        f"http://localhost:8000/api/materials/{material_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    material = response.json()
    status = material["processing_status"]
    
    print(f"Status: {status}")
    
    if status == "completed":
        print(f"Processing completed at: {material['processed_at']}")
        print(f"Has embedding: {material['has_embedding']}")
        break
    elif status == "failed":
        print(f"Processing failed: {material['error_message']}")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

### Example 2: Semantic Search

```python
import requests

# Search for materials about a topic
response = requests.get(
    f"http://localhost:8000/api/courses/{course_id}/materials/search",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "query": "What is gradient descent?",
        "limit": 3
    }
)

results = response.json()

print(f"Found {len(results)} relevant materials:")
for result in results:
    print(f"\n{result['name']} (Score: {result['similarity_score']:.2f})")
    print(f"Excerpt: {result['excerpt'][:200]}...")
```

### Example 3: Chat with RAG

```python
import requests

# Send chat message with course context
response = requests.post(
    f"http://localhost:8000/api/courses/{course_id}/chat",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "message": "Explain the backpropagation algorithm",
        "history": [],
        "attachments": []
    }
)

chat_response = response.json()
print(f"AI Response: {chat_response['response']}")
print(f"Timestamp: {chat_response['timestamp']}")
```

### Example 4: Frontend Integration (React)

```typescript
// Upload material with progress tracking
const uploadMaterial = async (courseId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`/api/courses/${courseId}/materials`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const material = await response.json();
  
  // Poll for processing completion
  const checkStatus = async () => {
    const statusResponse = await fetch(`/api/materials/${material.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const updated = await statusResponse.json();
    
    if (updated.processing_status === 'completed') {
      console.log('Processing complete!');
      return updated;
    } else if (updated.processing_status === 'failed') {
      console.error('Processing failed:', updated.error_message);
      return updated;
    } else {
      // Still processing, check again in 5 seconds
      setTimeout(checkStatus, 5000);
    }
  };
  
  checkStatus();
  return material;
};

// Semantic search
const searchMaterials = async (courseId: string, query: string) => {
  const response = await fetch(
    `/api/courses/${courseId}/materials/search?query=${encodeURIComponent(query)}&limit=3`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
};

// Chat with RAG
const chatWithRAG = async (courseId: string, message: string, history: any[]) => {
  const response = await fetch(`/api/courses/${courseId}/chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      history,
      attachments: []
    })
  });
  
  return await response.json();
};
```

---

## Processing Workflow

### Upload Flow

```
1. User uploads file
   ↓
2. Validate file type and size
   ↓
3. Upload to Supabase Storage
   ↓
4. Create database record (status: 'pending')
   ↓
5. Queue background processing task
   ↓
6. Return immediately to user
```

### Background Processing Flow

```
1. Update status to 'processing'
   ↓
2. Download file from storage
   ↓
3. Send to AI Brain /router endpoint
   ↓
4. AI Brain extracts text using qwen3-vl:2b
   ↓
5. Store extracted_text in database
   ↓
6. Send text to AI Brain /utility/embed endpoint
   ↓
7. AI Brain generates embedding using mxbai-embed-large
   ↓
8. Store embedding (384 dimensions) in database
   ↓
9. Update status to 'completed' with timestamp
   ↓
10. If any step fails: Update status to 'failed' with error_message
```

### Search Flow

```
1. User submits search query
   ↓
2. Validate course ownership
   ↓
3. Generate embedding for query using AI Brain
   ↓
4. Perform vector similarity search using pgvector
   ↓
5. Return top N results ranked by similarity score
```

### RAG Flow

```
1. User sends chat message with course_id
   ↓
2. Perform semantic search using message as query
   ↓
3. Retrieve top 3 relevant material excerpts
   ↓
4. Augment prompt with material context
   ↓
5. Send to AI Brain for response generation
   ↓
6. Return AI response to user
   ↓
7. Save conversation to chat_history
```

---

## Error Handling

### Processing Errors

| Error Type | Status Update | Retry Behavior |
|------------|---------------|----------------|
| OCR Failure | `failed` with error_message | Manual retry via re-upload |
| Embedding Failure | `failed` with error_message | Manual retry via re-upload |
| Timeout (>5 min) | `failed` with "Processing timeout" | Manual retry via re-upload |
| Storage Error | `failed` with error details | Automatic retry (3 attempts) |
| AI Brain Unavailable | `failed` with "Service unavailable" | Manual retry after service starts |

### API Error Responses

#### 400 Bad Request
```json
{
  "detail": "File type image/bmp not allowed"
}
```

#### 404 Not Found
```json
{
  "detail": "Course not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to search materials: Connection timeout"
}
```

#### 503 Service Unavailable
```json
{
  "error": "AI Brain service not available",
  "code": "LOCAL_AI_API_ERROR"
}
```

### Logging

All errors are logged with detailed information:

```python
logger.error(f"Material processing failed for {material_id}: {e}", exc_info=True)
```

Log levels:
- `INFO`: Normal operations (upload, search, completion)
- `WARNING`: Non-critical issues (AI Brain unavailable on startup)
- `ERROR`: Processing failures, API errors

---

## Testing

### Unit Tests

Run unit tests for individual components:

```bash
# Test AI Brain client
pytest python-backend/test_ai_brain_client.py -v

# Test material processing service
pytest python-backend/test_material_processing_service.py -v

# Test background queue
pytest python-backend/test_background_queue.py -v

# Test search endpoint
pytest python-backend/test_search_endpoint.py -v

# Test RAG integration
pytest python-backend/test_rag_integration.py -v
```

### Property-Based Tests

Run property-based tests using Hypothesis:

```bash
# Test OCR property
pytest python-backend/test_ai_brain_ocr_property.py -v

# Test embedding property
pytest python-backend/test_ai_brain_embedding_property.py -v

# Test embedding structure
pytest python-backend/test_embedding_structure.py -v
```

### Integration Tests

Run end-to-end integration tests:

```bash
# Test material endpoints
pytest python-backend/test_material_endpoints.py -v

# Test material search
pytest python-backend/test_material_search.py -v
```

### Manual Testing

#### Test Upload and Processing

```bash
# 1. Start AI Brain service
cd ai-brain
source venv/bin/activate
python brain.py

# 2. Start backend (in another terminal)
cd python-backend
source venv/bin/activate
uvicorn main:app --reload

# 3. Upload a test file
curl -X POST "http://localhost:8000/api/courses/{course_id}/materials" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test-document.pdf"

# 4. Check processing status
curl -X GET "http://localhost:8000/api/materials/{material_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Test Semantic Search

```bash
# Search for materials
curl -X GET "http://localhost:8000/api/courses/{course_id}/materials/search?query=machine%20learning&limit=3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Test RAG

```bash
# Chat with course context
curl -X POST "http://localhost:8000/api/courses/{course_id}/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is supervised learning?",
    "history": [],
    "attachments": []
  }'
```

---

## Troubleshooting

### Issue: Materials stuck in "pending" status

**Cause**: AI Brain service not running or not accessible

**Solution**:
1. Check if AI Brain service is running:
   ```bash
   curl http://localhost:8001/
   ```
2. Start AI Brain service if not running:
   ```bash
   cd ai-brain
   source venv/bin/activate
   python brain.py
   ```
3. Check backend logs for connection errors
4. Verify `AI_BRAIN_ENDPOINT` in `.env` is correct

### Issue: Processing fails with timeout

**Cause**: Large files or slow OCR processing

**Solution**:
1. Increase timeout in `.env`:
   ```bash
   AI_BRAIN_TIMEOUT=600  # 10 minutes
   MATERIAL_PROCESSING_TIMEOUT=600
   ```
2. Restart backend
3. Re-upload the material

### Issue: Search returns no results

**Possible Causes**:
1. No materials have been processed yet (check `processing_status`)
2. Materials failed processing (check `error_message`)
3. Query doesn't match material content semantically

**Solution**:
1. Check material status:
   ```bash
   curl -X GET "http://localhost:8000/api/courses/{course_id}/materials" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
2. Verify materials have `processing_status: "completed"` and `has_embedding: true`
3. Try broader search queries
4. Check backend logs for search errors

### Issue: RAG not including material context

**Cause**: No relevant materials found or search failing

**Solution**:
1. Test semantic search directly to verify materials are searchable
2. Check backend logs for RAG-related warnings
3. Verify materials are processed and have embeddings
4. Try more specific questions related to material content

### Issue: "Vector dimension mismatch" error

**Cause**: Migration used wrong embedding dimension

**Solution**:
1. Check migration file uses `VECTOR(384)` (not 1024)
2. Re-run migration if needed:
   ```sql
   ALTER TABLE materials DROP COLUMN embedding;
   ALTER TABLE materials ADD COLUMN embedding VECTOR(384);
   CREATE INDEX idx_materials_embedding ON materials USING hnsw (embedding vector_cosine_ops);
   ```

### Issue: High memory usage

**Cause**: AI Brain models consuming VRAM

**Solution**:
1. AI Brain automatically unloads specialist models after use
2. Restart AI Brain service to clear memory:
   ```bash
   # Stop with Ctrl+C, then restart
   python brain.py
   ```
3. Consider using smaller models if available
4. Process materials in smaller batches

### Issue: Slow search performance

**Cause**: Missing or inefficient index

**Solution**:
1. Verify HNSW index exists:
   ```sql
   SELECT indexname FROM pg_indexes 
   WHERE tablename = 'materials' 
   AND indexname = 'idx_materials_embedding';
   ```
2. Rebuild index if needed:
   ```sql
   REINDEX INDEX idx_materials_embedding;
   ```
3. Consider adjusting HNSW parameters for your dataset size

### Getting Help

If you encounter issues not covered here:

1. Check backend logs: `python-backend/logs/`
2. Check AI Brain logs in the terminal where it's running
3. Enable debug logging in `.env`:
   ```bash
   LOG_LEVEL=DEBUG
   ```
4. Review the design document: `.kiro/specs/material-ocr-embedding/design.md`
5. Review the requirements: `.kiro/specs/material-ocr-embedding/requirements.md`

---

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Process multiple materials in parallel when possible
2. **Result Limiting**: Keep search limit low (3-5) for faster responses
3. **Index Maintenance**: Periodically rebuild HNSW index for optimal performance
4. **Caching**: Consider caching frequently searched query embeddings
5. **File Size**: Compress large PDFs before upload to reduce processing time

### Expected Performance

| Operation | Expected Time |
|-----------|---------------|
| Upload (10MB file) | < 1 second |
| OCR (10-page PDF) | 30-60 seconds |
| Embedding generation | 1-2 seconds |
| Semantic search | < 500ms |
| RAG chat response | 2-5 seconds |

### Scaling Considerations

For production deployments with high volume:

1. **Queue System**: Replace FastAPI BackgroundTasks with Celery or RQ
2. **Distributed Processing**: Run multiple AI Brain instances
3. **Database**: Use connection pooling and read replicas
4. **Caching**: Add Redis for query embedding cache
5. **CDN**: Serve files from CDN instead of Supabase Storage

---

## Security Considerations

### File Upload Security

1. **File Type Validation**: Only allow whitelisted MIME types
2. **File Size Limits**: Enforce maximum file size (default: 10MB)
3. **Virus Scanning**: Consider adding virus scanning for production
4. **Storage Isolation**: Files stored per user/course to prevent access leaks

### Access Control

1. **Course Ownership**: All endpoints verify course ownership
2. **JWT Authentication**: Required for all material operations
3. **RLS Policies**: Supabase Row Level Security enforces data isolation

### API Security

1. **Rate Limiting**: Implemented on chat and search endpoints
2. **Input Validation**: All inputs validated using Pydantic schemas
3. **Error Messages**: Don't expose internal details in error responses
4. **Logging**: Sensitive data excluded from logs

---

## Next Steps

### Phase 2 Enhancements (Future)

The current implementation uses a local AI Brain service. Future enhancements may include:

1. **Multiple AI Providers**: Support for Gemini, OpenAI, Anthropic
2. **Provider Abstraction**: Abstract interface for swapping providers
3. **Hybrid Processing**: Use cloud APIs for faster processing
4. **Advanced RAG**: Multi-query retrieval, re-ranking, citation tracking
5. **Batch Operations**: Bulk upload and processing
6. **Progress Tracking**: Real-time progress updates via WebSocket
7. **Material Management**: Edit extracted text, regenerate embeddings
8. **Analytics**: Track search patterns, material usage statistics

### Migration Path

To migrate to cloud AI providers in the future:

1. Implement provider interface (already designed in architecture)
2. Add provider-specific clients (Gemini, OpenAI, etc.)
3. Update configuration to select provider
4. No changes needed to API endpoints or database schema
5. Existing embeddings remain compatible (same dimension)

---

## Additional Resources

- **Design Document**: `.kiro/specs/material-ocr-embedding/design.md`
- **Requirements**: `.kiro/specs/material-ocr-embedding/requirements.md`
- **Tasks**: `.kiro/specs/material-ocr-embedding/tasks.md`
- **AI Brain Client**: `python-backend/services/AI_BRAIN_CLIENT_README.md`
- **Material Processing Service**: `python-backend/services/MATERIAL_PROCESSING_SERVICE_README.md`
- **Configuration Guide**: `python-backend/CONFIGURATION_GUIDE.md`

---

## Quick Reference

### Common Commands

```bash
# Start AI Brain service
cd ai-brain && source venv/bin/activate && python brain.py

# Start backend
cd python-backend && source venv/bin/activate && uvicorn main:app --reload

# Run all tests
pytest python-backend/ -v

# Check material status
curl -X GET "http://localhost:8000/api/materials/{material_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search materials
curl -X GET "http://localhost:8000/api/courses/{course_id}/materials/search?query=YOUR_QUERY" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Status Codes

- `200 OK`: Successful GET/DELETE
- `201 Created`: Successful POST
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: AI Brain service unavailable

### File Type Support

- **PDFs**: `application/pdf`
- **Images**: `image/jpeg`, `image/png`, `image/gif`, `image/webp`

### Embedding Dimensions

- **Current**: 384 (mxbai-embed-large via AI Brain)
- **Database**: VECTOR(384)
- **Search**: Cosine similarity

---

*Last Updated: December 2024*
*Feature Version: 1.0*
