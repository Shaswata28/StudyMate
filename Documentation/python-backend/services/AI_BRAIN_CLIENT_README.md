# AI Brain Client

Client library for communicating with the local AI Brain service for OCR text extraction and embedding generation.

## Overview

The AI Brain Client provides a simple interface to interact with the AI Brain service (running on port 8001), which orchestrates specialized Ollama models:

- **qwen3-vl:2b**: Vision-language model for OCR text extraction from images and PDFs
- **mxbai-embed-large**: Embedding model for generating 1024-dimensional semantic vectors

## Features

- **Text Extraction**: Extract text from PDFs and images using OCR
- **Embedding Generation**: Generate semantic vector embeddings from text
- **Health Checks**: Verify AI Brain service availability
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Timeout Configuration**: Configurable timeouts for long-running operations
- **Async Support**: Fully async/await compatible

## Installation

The AI Brain client is included in the services package. No additional installation required.

## Configuration

Configure the AI Brain client using environment variables:

```bash
# .env file
AI_BRAIN_ENDPOINT=http://localhost:8001
AI_BRAIN_TIMEOUT=300.0  # 5 minutes for OCR processing
```

## Usage

### Basic Initialization

```python
from services.ai_brain_client import AIBrainClient, AIBrainClientError

# Initialize with defaults
client = AIBrainClient()

# Initialize with custom configuration
client = AIBrainClient(
    brain_endpoint="http://localhost:8001",
    timeout=300.0  # 5 minutes
)
```

### Health Check

```python
# Check if AI Brain service is available
is_healthy = await client.health_check()

if is_healthy:
    print("AI Brain service is running")
else:
    print("AI Brain service is unavailable")
```

### Text Extraction (OCR)

```python
# Extract text from a file
try:
    with open("document.pdf", "rb") as f:
        file_data = f.read()
    
    extracted_text = await client.extract_text(
        file_data=file_data,
        filename="document.pdf",
        prompt="Extract all text from this document"
    )
    
    print(f"Extracted {len(extracted_text)} characters")
    
except AIBrainClientError as e:
    print(f"Text extraction failed: {e}")
```

### Embedding Generation

```python
# Generate embedding from text
try:
    text = "This is a sample text for embedding generation."
    
    embedding = await client.generate_embedding(text)
    
    print(f"Generated embedding with {len(embedding)} dimensions")
    
except AIBrainClientError as e:
    print(f"Embedding generation failed: {e}")
```

## Error Handling

The client raises `AIBrainClientError` for all failures:

```python
from services.ai_brain_client import AIBrainClientError

try:
    result = await client.extract_text(file_data, filename)
except AIBrainClientError as e:
    # Handle specific error cases
    if "unavailable" in str(e):
        print("AI Brain service is not running")
    elif "timeout" in str(e):
        print("Operation timed out")
    else:
        print(f"Error: {e}")
```

## Common Error Scenarios

### Service Unavailable

```
AIBrainClientError: AI Brain service unavailable: All connection attempts failed
```

**Solution**: Ensure the AI Brain service is running:
```bash
cd ai-brain
python brain.py
```

### Timeout

```
AIBrainClientError: Text extraction timeout after 300.0s
```

**Solution**: Increase timeout for large files:
```python
client = AIBrainClient(timeout=600.0)  # 10 minutes
```

### Empty Text

```
AIBrainClientError: Cannot generate embedding for empty text
```

**Solution**: Validate text before generating embeddings:
```python
if text and text.strip():
    embedding = await client.generate_embedding(text)
```

## Integration with Material Processing

The AI Brain client is designed to be used by the Material Processing Service:

```python
from services.ai_brain_client import AIBrainClient
from config import config

# Initialize client with configuration
ai_brain_client = AIBrainClient(
    brain_endpoint=config.AI_BRAIN_ENDPOINT,
    timeout=config.AI_BRAIN_TIMEOUT
)

# Use in material processing
async def process_material(material_id: str):
    # Download file
    file_data = await download_file(material_id)
    
    # Extract text
    extracted_text = await ai_brain_client.extract_text(
        file_data=file_data,
        filename="material.pdf"
    )
    
    # Generate embedding
    if extracted_text.strip():
        embedding = await ai_brain_client.generate_embedding(extracted_text)
    
    # Store results
    await store_results(material_id, extracted_text, embedding)
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest test_ai_brain_client.py -v

# Run specific test
python -m pytest test_ai_brain_client.py::test_health_check_success -v
```

Verify the client is working:

```bash
# Ensure AI Brain service is running first
python verify_ai_brain_client.py
```

## API Reference

### AIBrainClient

#### `__init__(brain_endpoint: str = "http://localhost:8001", timeout: float = 300.0)`

Initialize the AI Brain client.

**Parameters:**
- `brain_endpoint`: Base URL of the AI Brain service
- `timeout`: Request timeout in seconds (default: 300.0)

#### `async health_check() -> bool`

Check if AI Brain service is available.

**Returns:** `True` if service is healthy, `False` otherwise

#### `async extract_text(file_data: bytes, filename: str, prompt: str = "Extract all text from this document") -> str`

Extract text from a file using OCR.

**Parameters:**
- `file_data`: File content as bytes
- `filename`: Original filename (for content type detection)
- `prompt`: Instruction prompt for OCR

**Returns:** Extracted text as string

**Raises:** `AIBrainClientError` if extraction fails

#### `async generate_embedding(text: str) -> list[float]`

Generate vector embedding from text.

**Parameters:**
- `text`: Text content to embed

**Returns:** Embedding vector (1024 dimensions)

**Raises:** `AIBrainClientError` if generation fails

### AIBrainClientError

Exception raised for all AI Brain client errors.

## Requirements

- Python 3.10+
- httpx (async HTTP client)
- AI Brain service running on configured endpoint

## Related Documentation

- [AI Brain Service](../../ai-brain/README.md)
- [Material Processing Service](./material_processing_service.py)
- [Design Document](../.kiro/specs/material-ocr-embedding/design.md)
