# AI Provider Abstraction Layer

## Overview

The AI Provider abstraction layer provides a unified interface for different AI services (Gemini, Router, etc.) to handle OCR, embeddings, and chat functionality. This design allows switching between providers with minimal code changes.

## Architecture

```
┌─────────────────────────────────────┐
│      Application Code               │
│  (Materials Service, Chat Router)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    AI Provider Factory              │
│    get_ai_provider()                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    AIProvider (Abstract Interface)  │
│    - extract_text()                 │
│    - generate_embedding()           │
│    - chat_with_context()            │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│   Gemini    │  │   Router    │
│  Provider   │  │  Provider   │
│  (Phase 1)  │  │  (Phase 2)  │
└─────────────┘  └─────────────┘
```

## Components

### 1. AIProvider (Abstract Interface)

**File:** `services/ai_provider.py`

Defines the contract that all AI providers must implement:

- `extract_text(file_data: bytes, mime_type: str) -> str`
  - Extract text from files using OCR
  - Returns empty string if no text found
  
- `generate_embedding(text: str) -> List[float]`
  - Generate 384-dimensional vector embeddings
  - Used for semantic search
  
- `chat_with_context(message: str, context: List[str], history: Optional[List]) -> str`
  - Generate chat responses with RAG context
  - Includes material excerpts in the prompt

### 2. AI Provider Factory

**File:** `services/ai_provider_factory.py`

Factory function that creates the appropriate provider based on configuration:

```python
from services.ai_provider_factory import get_ai_provider

# Get the configured provider (singleton)
provider = get_ai_provider()

# Use the provider
text = await provider.extract_text(file_data, "application/pdf")
embedding = await provider.generate_embedding(text)
response = await provider.chat_with_context(message, context)
```

### 3. Configuration

**File:** `config.py`

Configuration variables for AI providers:

```bash
# Choose provider
AI_PROVIDER=gemini  # or "router"

# Gemini configuration (when AI_PROVIDER=gemini)
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=models/embedding-001

# Router configuration (when AI_PROVIDER=router)
ROUTER_ENDPOINT=https://your-colab-endpoint.com
ROUTER_API_KEY=your_key

# Processing configuration
MATERIAL_PROCESSING_TIMEOUT=300
MAX_EMBEDDING_DIMENSION=384
SEARCH_RESULT_LIMIT=3
```

## Usage Example

```python
from services.ai_provider_factory import get_ai_provider

async def process_material(file_data: bytes, mime_type: str):
    """Process a material file with OCR and embedding generation."""
    
    # Get the configured provider
    provider = get_ai_provider()
    
    try:
        # Extract text
        text = await provider.extract_text(file_data, mime_type)
        
        # Generate embedding
        if text:
            embedding = await provider.generate_embedding(text)
            return text, embedding
        else:
            return "", None
            
    except AIProviderError as e:
        logger.error(f"Processing failed: {e}")
        raise
```

## Provider Implementations

### Phase 1: Gemini Provider

**Status:** To be implemented in Task 3

Will use Google Gemini API for:
- OCR: Gemini vision/PDF capabilities
- Embeddings: Gemini embedding model (384 dimensions)
- Chat: Gemini chat with RAG context

### Phase 2: Router Provider

**Status:** Future implementation (Task 13)

Will use router-based architecture with specialized models:
- OCR: DeepSeek model in Google Colab
- Chat: Llama 3.2 for general queries
- Code: Qwen Coder 2.5 for code-related queries
- Embeddings: Specialized embedding model

## Switching Providers

To switch providers, simply update the configuration:

```bash
# Switch from Gemini to Router
AI_PROVIDER=router
ROUTER_ENDPOINT=https://your-endpoint.com
ROUTER_API_KEY=your_key
```

No code changes required! The factory will automatically create the correct provider instance.

## Testing

Run the configuration test:

```bash
python test_ai_provider_config.py
```

This verifies:
- Configuration loads correctly
- Factory creates provider instances
- All required settings are present

## Error Handling

All providers raise `AIProviderError` for failures:

```python
from services.ai_provider import AIProviderError

try:
    text = await provider.extract_text(file_data, mime_type)
except AIProviderError as e:
    # Handle provider-specific errors
    logger.error(f"OCR failed: {e}")
```

## Next Steps

1. **Task 3:** Implement GeminiProvider class
2. **Task 4:** Create MaterialProcessingService using the provider
3. **Task 13:** Implement RouterProvider class (Phase 2)
