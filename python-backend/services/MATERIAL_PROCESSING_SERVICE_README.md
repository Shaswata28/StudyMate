# Material Processing Service

## Overview

The `MaterialProcessingService` handles the background processing of uploaded materials (PDFs, images) by:
1. Extracting text using AI Brain OCR (qwen3-vl:2b model)
2. Generating semantic embeddings using AI Brain (mxbai-embed-large model)
3. Tracking processing status through state transitions
4. Handling errors and timeouts gracefully

## Architecture

```
Material Upload → Background Task → MaterialProcessingService
                                           ↓
                                    AI Brain Client
                                           ↓
                                    ┌──────┴──────┐
                                    ↓             ↓
                                  OCR         Embedding
                              (qwen3-vl)   (mxbai-embed)
                                    ↓             ↓
                                    └──────┬──────┘
                                           ↓
                                    Update Database
```

## Status Flow

```
pending → processing → completed
                    ↘ failed
```

- **pending**: Material uploaded, waiting for processing
- **processing**: Currently being processed (OCR + embedding)
- **completed**: Successfully processed with text and embedding stored
- **failed**: Processing failed (error_message contains details)

## Usage

### Initialization

```python
from services.ai_brain_client import AIBrainClient
from services.material_processing_service import MaterialProcessingService
from config import config

# Initialize AI Brain client
ai_brain_client = AIBrainClient(
    brain_endpoint=config.AI_BRAIN_ENDPOINT,
    timeout=config.AI_BRAIN_TIMEOUT
)

# Initialize processing service
processing_service = MaterialProcessingService(
    ai_brain_client=ai_brain_client,
    timeout=300.0  # 5 minutes
)
```

### Processing a Material

```python
# In a background task
await processing_service.process_material(material_id="uuid-here")
```

### Integration with FastAPI Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/courses/{course_id}/materials")
async def upload_material(
    course_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user: AuthUser = Depends(get_current_user)
):
    # ... upload file and create database record ...
    
    # Queue background processing
    background_tasks.add_task(
        processing_service.process_material,
        material_id=material_data["id"]
    )
    
    # Return immediately with pending status
    return MaterialResponse(...)
```

## Error Handling

The service handles multiple error scenarios:

### 1. AI Brain Service Unavailable
- **Error**: Connection refused, service not running
- **Action**: Status set to 'failed', error_message logged
- **Recovery**: Restart AI Brain service, retry processing

### 2. OCR Timeout
- **Error**: Text extraction exceeds timeout (default: 5 minutes)
- **Action**: Status set to 'failed', timeout error logged
- **Recovery**: Increase timeout or optimize file size

### 3. Embedding Generation Failure
- **Error**: Empty text or service error
- **Action**: Status set to 'failed', error details logged
- **Recovery**: Check text extraction, verify AI Brain service

### 4. Storage Download Failure
- **Error**: File not found in Supabase Storage
- **Action**: Status set to 'failed', storage error logged
- **Recovery**: Verify file upload, check storage permissions

### 5. Empty Text Content
- **Behavior**: Not an error - status set to 'completed'
- **Action**: extracted_text stored as empty string, no embedding generated
- **Use Case**: Blank pages, images without text

## Database Schema

The service updates the following columns in the `materials` table:

```sql
-- Status tracking
processing_status TEXT CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
processed_at TIMESTAMPTZ
error_message TEXT

-- Extracted data
extracted_text TEXT
embedding VECTOR(1024)  -- mxbai-embed-large dimensions
```

## Logging

The service provides detailed logging at multiple levels:

```python
# Info level
logger.info("Starting material processing: {material_id}")
logger.info("Text extraction completed: {len} characters extracted")
logger.info("Material processing completed successfully: {material_id}")

# Warning level
logger.warning("Material not found: {material_id}")

# Error level
logger.error("Material {material_id}: AI Brain service error: {error}")
logger.error("Material {material_id}: Unexpected processing error", exc_info=True)
```

## Performance Considerations

1. **Async Processing**: All operations are async to avoid blocking
2. **Timeout Handling**: Configurable timeouts prevent indefinite hangs
3. **Resource Management**: AI Brain service manages model loading/unloading
4. **Error Recovery**: Failed materials can be reprocessed by resetting status to 'pending'

## Configuration

Environment variables (in `.env`):

```bash
# AI Brain Service
AI_BRAIN_ENDPOINT=http://localhost:8001
AI_BRAIN_TIMEOUT=300.0  # 5 minutes

# Supabase (for storage and database)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Testing

See property-based tests for validation:
- `test_ai_brain_ocr_property.py` - OCR extraction properties
- `test_ai_brain_embedding_property.py` - Embedding generation properties

## Requirements Validation

This service implements the following requirements:

- **1.2**: Background processing initiated on upload
- **1.3**: Status updated to 'processing' when processing begins
- **1.4**: Extracted text and embeddings stored on success
- **1.5**: Status updated to 'completed' with timestamp
- **2.3**: Extracted text stored in materials table
- **2.4**: Failed extraction updates status to 'failed' with error
- **3.2**: Embeddings stored as VECTOR(1024)
- **3.4**: Failed embedding generation updates status with error
- **8.1**: Async processing doesn't block upload response
- **8.2**: Detailed error logging for debugging
- **8.3**: Failed processing updates status with error details
- **8.4**: Timeout handling marks materials as failed

## Troubleshooting

### Material stuck in 'processing' status
- Check AI Brain service logs
- Verify timeout configuration
- Check for network issues
- Manually reset status to 'pending' to retry

### All materials failing with "AI Brain service unavailable"
- Verify AI Brain service is running on port 8001
- Check `AI_BRAIN_ENDPOINT` configuration
- Test with: `curl http://localhost:8001/`

### OCR extracting no text from valid documents
- Verify file is not corrupted
- Check AI Brain service logs for model errors
- Test OCR directly via AI Brain `/router` endpoint

### Embedding generation failing
- Verify extracted text is not empty
- Check AI Brain service has mxbai-embed-large model
- Test embedding directly via AI Brain `/utility/embed` endpoint
