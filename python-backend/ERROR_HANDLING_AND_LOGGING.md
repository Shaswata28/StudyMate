# Error Handling and Logging Documentation

## Overview

This document describes the comprehensive error handling and logging system implemented for the material processing pipeline. The system provides detailed debugging information, automatic retry logic for transient failures, and proper error categorization.

## Error Categories

### Material Processing Errors

The system uses a hierarchy of exception classes to categorize different types of errors:

1. **MaterialProcessingError** (Base)
   - Base exception for all material processing errors
   - Used for general processing failures

2. **MaterialNotFoundError**
   - Raised when a material cannot be found in the database
   - Typically indicates an invalid material ID

3. **StorageDownloadError**
   - Raised when file download from Supabase Storage fails
   - Can be caused by network issues, missing files, or permission problems

4. **OCRProcessingError**
   - Raised when OCR text extraction fails
   - Can be caused by AI Brain service issues or unsupported file formats

5. **EmbeddingGenerationError**
   - Raised when embedding generation fails
   - Can be caused by AI Brain service issues or invalid text input

6. **DatabaseUpdateError**
   - Raised when database operations fail
   - Can be caused by network issues or database constraints

### AI Brain Client Errors

**AIBrainClientError**
- Base exception for all AI Brain client errors
- Includes connection errors, timeouts, and HTTP errors

## Retry Logic

### Configuration

Retry behavior is configured via environment variables:

```bash
# Maximum number of retry attempts (default: 3)
MAX_RETRY_ATTEMPTS=3

# Initial delay before first retry in seconds (default: 2.0)
RETRY_DELAY_SECONDS=2.0

# Exponential backoff multiplier (default: 2.0)
RETRY_BACKOFF_MULTIPLIER=2.0
```

### Retry Strategy

The system uses exponential backoff for retries:
- Attempt 1: Immediate
- Attempt 2: After 2 seconds
- Attempt 3: After 4 seconds
- Attempt 4: After 8 seconds (if MAX_RETRY_ATTEMPTS=4)

### When Retries Occur

**AI Brain Client (extract_text and generate_embedding):**
- ✅ Connection errors (httpx.ConnectError) - Always retry
- ✅ Server errors (5xx HTTP status) - Always retry
- ✅ Timeout errors for embeddings - Always retry
- ❌ Timeout errors for OCR - No retry (likely file is too large/complex)
- ❌ Client errors (4xx HTTP status) - No retry (invalid request)

**Storage Downloads:**
- ✅ All storage download failures - Always retry (transient network issues)

### Disabling Retries

You can disable retries for specific operations by passing `retry_on_failure=False`:

```python
# Disable retries for this specific call
text = await ai_brain_client.extract_text(
    file_data=data,
    filename="test.pdf",
    retry_on_failure=False
)
```

## Logging

### Log Levels

The system uses standard Python logging levels:

- **INFO**: Normal operation flow, successful completions
- **WARNING**: Non-critical issues, fallback behavior
- **ERROR**: Operation failures, exceptions
- **DEBUG**: Detailed debugging information (not currently used)

### Log Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example:
```
2024-12-06 10:30:45,123 - services.material_processing_service - INFO - Starting material processing: abc-123
```

### Detailed Logging for Material Processing

Material processing includes comprehensive logging:

```
============================================================
Starting material processing: abc-123
Start time: 2024-12-06T10:30:45.123456+00:00
============================================================
Material abc-123: Status updated to 'processing'
Material abc-123: Retrieved metadata - Name: lecture.pdf, Type: application/pdf, Size: 1048576 bytes
Material abc-123: Downloading file from storage: user-id/course-id/lecture.pdf
Material abc-123: File downloaded successfully (1048576 bytes)
Material abc-123: Starting OCR text extraction (timeout: 300.0s)
Extracting text from file: lecture.pdf (1048576 bytes) [Attempt 1/3]
Text extraction completed successfully: 5432 characters extracted [Attempt 1/3]
Material abc-123: OCR completed in 45.23s - Extracted 5432 characters
Material abc-123: Starting embedding generation (timeout: 300.0s)
Generating embedding for text (5432 characters) [Attempt 1/3]
Embedding generated successfully (1024 dimensions) [Attempt 1/3]
Material abc-123: Embedding generated in 2.15s - Dimensions: 1024
Material abc-123: Updating database with processing results
Material abc-123 data updated: 5432 chars, embedding: 1024 dims
============================================================
Material processing completed successfully: abc-123 (Total time: 47.38s)
============================================================
```

### Detailed Logging for Semantic Search

Semantic search includes comprehensive logging:

```
============================================================
Starting semantic search in course xyz-789
Query: What is machine learning?
Limit: 3
============================================================
Generating embedding for search query
Generating embedding for text (26 characters) [Attempt 1/3]
Embedding generated successfully (1024 dimensions) [Attempt 1/3]
Query embedding generated in 1.23s (1024 dimensions)
Found 3 materials for query
============================================================
Semantic search completed successfully: 3 results (Total time: 1.45s)
============================================================
```

### Error Logging

Errors are logged with full stack traces for debugging:

```python
logger.error(f"Material {material_id}: {error_msg}", exc_info=True)
```

This includes:
- Error message
- Exception type
- Full stack trace
- Context information (material ID, operation, etc.)

## Error Handling Flow

### Material Processing Flow

```
1. Update status to 'processing'
   ↓
2. Get material record
   ↓ (MaterialNotFoundError)
3. Download file from storage
   ↓ (StorageDownloadError with retries)
4. Extract text with OCR
   ↓ (OCRProcessingError with retries, timeout handling)
5. Generate embedding
   ↓ (EmbeddingGenerationError with retries, timeout handling)
6. Update database
   ↓ (DatabaseUpdateError)
7. Update status to 'completed'
```

At each step, errors are:
1. Caught and categorized
2. Logged with full context
3. Retried if appropriate
4. Stored in the error_message field
5. Status updated to 'failed'

### Timeout Handling

Timeouts are handled at two levels:

1. **Operation-level timeout** (asyncio.wait_for)
   - Wraps the entire operation
   - Configured via AI_BRAIN_TIMEOUT (default: 300s)
   - Catches asyncio.TimeoutError

2. **HTTP-level timeout** (httpx.Timeout)
   - Configured in AIBrainClient
   - Catches httpx.TimeoutException
   - Subject to retry logic

## Best Practices

### For Developers

1. **Always log context**: Include material ID, operation name, and relevant parameters
2. **Use appropriate log levels**: INFO for normal flow, ERROR for failures
3. **Include timing information**: Log operation start/end times and durations
4. **Catch specific exceptions**: Use specific exception types for better error handling
5. **Don't swallow exceptions**: Always log exceptions with exc_info=True

### For Operations

1. **Monitor logs**: Watch for patterns of failures
2. **Adjust retry settings**: Tune MAX_RETRY_ATTEMPTS based on your environment
3. **Set appropriate timeouts**: Adjust AI_BRAIN_TIMEOUT based on file sizes
4. **Check error_message field**: Review failed materials in the database

## Monitoring and Debugging

### Key Metrics to Monitor

1. **Processing success rate**: Ratio of completed to failed materials
2. **Average processing time**: Time from pending to completed
3. **Retry frequency**: How often retries are triggered
4. **Timeout frequency**: How often operations timeout
5. **Error types**: Distribution of error categories

### Debugging Failed Materials

1. Check the `error_message` field in the materials table
2. Search logs for the material ID
3. Look for retry attempts and their outcomes
4. Check timing information to identify bottlenecks
5. Verify AI Brain service health

### Common Issues and Solutions

**Issue: Frequent connection errors**
- Solution: Check AI Brain service is running, verify endpoint configuration

**Issue: Frequent timeouts**
- Solution: Increase AI_BRAIN_TIMEOUT, check file sizes, verify system resources

**Issue: All retries exhausted**
- Solution: Check network connectivity, verify service health, review logs for patterns

**Issue: Storage download failures**
- Solution: Verify Supabase credentials, check file paths, review storage permissions

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 2.4**: Failed processing updates status with error details ✅
- **Requirement 3.4**: Embedding failures update status with error details ✅
- **Requirement 8.2**: Detailed error logging for debugging ✅
- **Requirement 8.3**: Errors captured in error_message field ✅

Additional features:
- Retry logic for transient failures (network issues, temporary service unavailability)
- Exponential backoff for retries
- Comprehensive timing and performance logging
- Error categorization for better debugging
- Configurable retry behavior via environment variables
