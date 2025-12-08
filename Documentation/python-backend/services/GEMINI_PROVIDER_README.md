# Gemini Provider Implementation

## Overview

The `GeminiProvider` class implements the `AIProvider` interface using Google's Gemini API. It provides three core capabilities:

1. **OCR (Optical Character Recognition)**: Extract text from PDFs and images
2. **Embedding Generation**: Create semantic vector embeddings from text
3. **RAG-enabled Chat**: Generate AI responses with material context

## Implementation Details

### Class: `GeminiProvider`

Located in: `python-backend/services/gemini_provider.py`

#### Initialization

```python
provider = GeminiProvider(
    api_key="your_gemini_api_key",
    model="gemini-1.5-flash",
    embedding_model="models/embedding-001",
    temperature=0.7,
    max_output_tokens=1024,
    timeout=30
)
```

#### Methods

##### 1. `extract_text(file_data: bytes, mime_type: str) -> str`

Extracts text from files using Gemini's vision/PDF capabilities.

**Supported MIME types:**
- `application/pdf` - PDF documents
- `image/jpeg` - JPEG images
- `image/png` - PNG images
- `image/gif` - GIF images
- `image/webp` - WebP images

**Returns:**
- Extracted text as a string
- Empty string if no text is found

**Raises:**
- `AIProviderError` if extraction fails

**Example:**
```python
with open("document.pdf", "rb") as f:
    file_data = f.read()

text = await provider.extract_text(file_data, "application/pdf")
print(f"Extracted: {text}")
```

##### 2. `generate_embedding(text: str) -> List[float]`

Generates a 384-dimensional vector embedding from text.

**Parameters:**
- `text`: Text content to embed (must not be empty)

**Returns:**
- List of 384 floats representing the embedding vector

**Raises:**
- `AIProviderError` if text is empty or generation fails

**Example:**
```python
text = "Machine learning is a subset of artificial intelligence."
embedding = await provider.generate_embedding(text)
print(f"Embedding dimensions: {len(embedding)}")  # 384
```

##### 3. `chat_with_context(message: str, context: List[str], history: Optional[List] = None) -> str`

Generates AI chat responses with optional material context (RAG).

**Parameters:**
- `message`: User's chat message
- `context`: List of material excerpts to use as context
- `history`: Optional conversation history (list of dicts with 'role' and 'parts')

**Returns:**
- AI-generated response text

**Raises:**
- `AIProviderError` if chat generation fails

**Example with context (RAG):**
```python
message = "What is machine learning?"
context = [
    "Machine learning is a subset of AI that enables systems to learn from data.",
    "Deep learning uses neural networks with multiple layers."
]

response = await provider.chat_with_context(message, context)
print(response)
```

**Example without context:**
```python
message = "What is 2 + 2?"
response = await provider.chat_with_context(message, [])
print(response)
```

## Error Handling

All methods raise `AIProviderError` for failures. Common error scenarios:

1. **Timeout**: Request exceeds configured timeout
2. **Quota Exceeded**: API rate limit reached
3. **Invalid Argument**: Invalid file format or empty text
4. **Permission Denied**: Authentication failure

All errors are logged with detailed information for debugging.

## Configuration

Configure via environment variables in `.env`:

```bash
# Required
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
GEMINI_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=models/embedding-001
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=1024
GEMINI_TIMEOUT=30
```

## Factory Usage

The recommended way to get a provider instance is through the factory:

```python
from services.ai_provider_factory import get_ai_provider

# Get configured provider (singleton)
provider = get_ai_provider()

# Use the provider
text = await provider.extract_text(file_data, mime_type)
embedding = await provider.generate_embedding(text)
response = await provider.chat_with_context(message, context)
```

## Testing

Run the test suite to verify the implementation:

```bash
cd python-backend
python test_gemini_provider.py
```

The test suite verifies:
- Provider initialization
- Embedding generation
- Empty text handling
- Chat with context (RAG)
- Chat without context

## Requirements Validation

This implementation satisfies the following requirements from the spec:

- **Requirement 2.1**: Extract text from PDF materials using OCR
- **Requirement 2.2**: Extract text from image materials using OCR
- **Requirement 3.1**: Generate vector embeddings from extracted text
- **Requirement 5.4**: Generate AI responses with material context
- **Requirement 7.4**: Implement provider interface for Gemini services

## Performance Considerations

1. **Async Operations**: All methods are async for non-blocking I/O
2. **Timeout Handling**: Configurable timeout prevents hanging requests
3. **Error Recovery**: Detailed error messages aid debugging
4. **Sliding Window**: Chat history limited to last 10 messages

## Security Considerations

1. **API Key Security**: Store in environment variables, never commit to code
2. **Error Messages**: Don't expose internal details to users
3. **Input Validation**: Validate file types and text before processing
4. **Rate Limiting**: Implement at application level to prevent quota exhaustion

## Future Enhancements (Phase 2)

When transitioning to the router architecture:

1. Keep this implementation for fallback/testing
2. Implement `RouterProvider` with same interface
3. Switch via configuration: `AI_PROVIDER=router`
4. No code changes required in consuming services

## Troubleshooting

### "Failed to initialize Gemini provider"
- Check that `GEMINI_API_KEY` is set in `.env`
- Verify API key is valid at https://makersuite.google.com/app/apikey

### "Text extraction failed"
- Verify file MIME type is supported
- Check file is not corrupted
- Ensure file size is within Gemini API limits

### "Embedding generation failed"
- Verify text is not empty
- Check API quota hasn't been exceeded
- Ensure text length is within limits

### "Chat generation failed"
- Check API quota
- Verify message and context are valid
- Review timeout settings if requests are slow
