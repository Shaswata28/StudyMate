# Material OCR & Embedding - Migration Guide

Guide for migrating to cloud AI providers and future enhancements.

## Current Architecture (Phase 1)

The current implementation uses a local AI Brain service:

```
┌─────────────────────────────────────────┐
│    Python Backend (FastAPI)             │
│  ┌───────────────────────────────────┐  │
│  │  Material Processing Service      │  │
│  │  - Uses AI Brain Client           │  │
│  └────────┬──────────────────────────┘  │
└───────────┼──────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│    AI Brain Service (Port 8001)         │
│  - qwen3-vl:2b (OCR)                    │
│  - mxbai-embed-large (Embeddings)       │
│  - Runs via Ollama                      │
└─────────────────────────────────────────┘
```

**Characteristics**:
- Local processing (no external API calls)
- Free (no API costs)
- Requires local GPU/CPU resources
- Embedding dimension: 384

## Future Architecture (Phase 2)

Support for multiple AI providers with abstract interface:

```
┌─────────────────────────────────────────┐
│    Python Backend (FastAPI)             │
│  ┌───────────────────────────────────┐  │
│  │  Material Processing Service      │  │
│  │  - Uses AI Provider Interface     │  │
│  └────────┬──────────────────────────┘  │
└───────────┼──────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│    AI Provider Interface (Abstract)     │
│  - extract_text()                       │
│  - generate_embedding()                 │
└────────┬────────────────────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
    │ Local  │    │ Gemini │    │ OpenAI │    │ Other  │
    │ Brain  │    │ API    │    │ API    │    │ APIs   │
    └────────┘    └────────┘    └────────┘    └────────┘
```

---

## Migration Path

### Step 1: Implement Provider Interface

Create abstract base class for AI providers:

```python
# services/ai_provider.py
from abc import ABC, abstractmethod
from typing import List

class AIProvider(ABC):
    """Abstract interface for AI providers"""
    
    @abstractmethod
    async def extract_text(self, file_data: bytes, filename: str) -> str:
        """Extract text from file using OCR"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding from text"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return embedding dimension for this provider"""
        pass
```

### Step 2: Implement Local Brain Provider

Wrap existing AI Brain client:

```python
# services/local_brain_provider.py
from services.ai_provider import AIProvider
from services.ai_brain_client import AIBrainClient

class LocalBrainProvider(AIProvider):
    """Local AI Brain provider implementation"""
    
    def __init__(self, brain_endpoint: str):
        self.client = AIBrainClient(brain_endpoint)
    
    async def extract_text(self, file_data: bytes, filename: str) -> str:
        return await self.client.extract_text(file_data, filename)
    
    async def generate_embedding(self, text: str) -> List[float]:
        return await self.client.generate_embedding(text)
    
    async def health_check(self) -> bool:
        return await self.client.health_check()
    
    @property
    def embedding_dimension(self) -> int:
        return 384  # mxbai-embed-large
```

### Step 3: Implement Gemini Provider

Add support for Google Gemini API:

```python
# services/gemini_provider.py
from services.ai_provider import AIProvider
import google.generativeai as genai
from typing import List

class GeminiProvider(AIProvider):
    """Google Gemini API provider implementation"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        self.embedding_model = 'models/text-embedding-004'
    
    async def extract_text(self, file_data: bytes, filename: str) -> str:
        """Extract text using Gemini Vision"""
        # Upload file to Gemini
        file = genai.upload_file(file_data, mime_type=self._get_mime_type(filename))
        
        # Generate text extraction
        response = await self.vision_model.generate_content_async([
            "Extract all text from this document",
            file
        ])
        
        return response.text
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini Embedding API"""
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    async def health_check(self) -> bool:
        try:
            # Test API connection
            genai.list_models()
            return True
        except Exception:
            return False
    
    @property
    def embedding_dimension(self) -> int:
        return 768  # text-embedding-004
```

### Step 4: Implement OpenAI Provider

Add support for OpenAI API:

```python
# services/openai_provider.py
from services.ai_provider import AIProvider
from openai import AsyncOpenAI
from typing import List
import base64

class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def extract_text(self, file_data: bytes, filename: str) -> str:
        """Extract text using GPT-4 Vision"""
        # Convert to base64
        base64_image = base64.b64encode(file_data).decode('utf-8')
        
        response = await self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text from this document"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI Embeddings API"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
    
    @property
    def embedding_dimension(self) -> int:
        return 1536  # text-embedding-3-small
```

### Step 5: Update Configuration

Add provider selection to config:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AI Provider Configuration
    AI_PROVIDER: str = "local"  # Options: local, gemini, openai
    
    # Local Brain Configuration
    AI_BRAIN_ENDPOINT: str = "http://localhost:8001"
    AI_BRAIN_TIMEOUT: int = 300
    
    # Gemini Configuration
    GEMINI_API_KEY: str = ""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
```

### Step 6: Implement Provider Factory

Create factory to instantiate providers:

```python
# services/ai_provider_factory.py
from services.ai_provider import AIProvider
from services.local_brain_provider import LocalBrainProvider
from services.gemini_provider import GeminiProvider
from services.openai_provider import OpenAIProvider
from config import settings

class AIProviderFactory:
    """Factory for creating AI provider instances"""
    
    @staticmethod
    def create_provider() -> AIProvider:
        """Create provider based on configuration"""
        provider_type = settings.AI_PROVIDER.lower()
        
        if provider_type == "local":
            return LocalBrainProvider(settings.AI_BRAIN_ENDPOINT)
        elif provider_type == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            return GeminiProvider(settings.GEMINI_API_KEY)
        elif provider_type == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            return OpenAIProvider(settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unknown AI provider: {provider_type}")
```

### Step 7: Update Material Processing Service

Use provider interface instead of direct client:

```python
# services/material_processing_service.py
from services.ai_provider import AIProvider

class MaterialProcessingService:
    """Handles background processing of uploaded materials"""
    
    def __init__(self, ai_provider: AIProvider, supabase_client):
        self.ai_provider = ai_provider  # Changed from ai_brain_client
        self.supabase = supabase_client
    
    async def process_material(self, material_id: str):
        """Process a material: extract text and generate embedding"""
        try:
            # ... existing code ...
            
            # Extract text using provider
            extracted_text = await self.ai_provider.extract_text(
                file_data=file_data,
                filename=material["name"]
            )
            
            # Generate embedding if text is not empty
            embedding = None
            if extracted_text.strip():
                embedding = await self.ai_provider.generate_embedding(extracted_text)
            
            # ... rest of existing code ...
```

### Step 8: Update Service Manager

Use factory to create provider:

```python
# services/service_manager.py
from services.ai_provider_factory import AIProviderFactory

class ServiceManager:
    def __init__(self):
        # Create AI provider using factory
        self.ai_provider = AIProviderFactory.create_provider()
        
        # Initialize processing service with provider
        self.processing_service = MaterialProcessingService(
            ai_provider=self.ai_provider,
            supabase_client=supabase
        )
```

---

## Database Migration for Different Embedding Dimensions

### Issue: Different Providers Use Different Dimensions

- Local Brain (mxbai-embed-large): 384 dimensions
- Gemini (text-embedding-004): 768 dimensions
- OpenAI (text-embedding-3-small): 1536 dimensions

### Solution 1: Separate Columns (Recommended)

Add provider-specific columns:

```sql
-- Add columns for different providers
ALTER TABLE materials 
ADD COLUMN embedding_local VECTOR(384),
ADD COLUMN embedding_gemini VECTOR(768),
ADD COLUMN embedding_openai VECTOR(1536),
ADD COLUMN embedding_provider TEXT;

-- Create indexes
CREATE INDEX idx_materials_embedding_local ON materials USING hnsw (embedding_local vector_cosine_ops);
CREATE INDEX idx_materials_embedding_gemini ON materials USING hnsw (embedding_gemini vector_cosine_ops);
CREATE INDEX idx_materials_embedding_openai ON materials USING hnsw (embedding_openai vector_cosine_ops);

-- Update search function to use correct column
CREATE OR REPLACE FUNCTION search_materials_by_embedding(
    p_course_id UUID,
    p_query_embedding VECTOR,
    p_provider TEXT,
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
    RETURN QUERY EXECUTE format(
        'SELECT 
            m.id AS material_id,
            m.name,
            LEFT(m.extracted_text, 500) AS excerpt,
            1 - (m.embedding_%s <=> $1) AS similarity_score,
            m.file_type
        FROM materials m
        WHERE m.course_id = $2
            AND m.embedding_%s IS NOT NULL
            AND m.processing_status = ''completed''
        ORDER BY m.embedding_%s <=> $1
        LIMIT $3',
        p_provider, p_provider, p_provider
    )
    USING p_query_embedding, p_course_id, p_limit;
END;
$$ LANGUAGE plpgsql;
```

### Solution 2: Dynamic Column (Alternative)

Use maximum dimension and pad smaller embeddings:

```sql
-- Use maximum dimension
ALTER TABLE materials 
ADD COLUMN embedding VECTOR(1536),
ADD COLUMN embedding_dimension INTEGER;

-- Pad smaller embeddings with zeros
-- Example: 384-dim embedding → pad to 1536 with zeros
```

---

## Migration Checklist

### Pre-Migration

- [ ] Backup database
- [ ] Document current configuration
- [ ] Test provider implementations
- [ ] Verify API keys and quotas
- [ ] Plan downtime window

### Migration Steps

- [ ] Implement provider interface
- [ ] Implement provider implementations
- [ ] Add provider factory
- [ ] Update material processing service
- [ ] Update configuration
- [ ] Run database migration
- [ ] Update search function
- [ ] Test with new provider
- [ ] Monitor processing status
- [ ] Verify search results

### Post-Migration

- [ ] Monitor error rates
- [ ] Check processing times
- [ ] Verify embedding quality
- [ ] Update documentation
- [ ] Train users on new features

---

## Provider Comparison

| Feature | Local Brain | Gemini | OpenAI |
|---------|-------------|--------|--------|
| **Cost** | Free | Pay per use | Pay per use |
| **Speed** | Depends on hardware | Fast | Fast |
| **OCR Quality** | Good | Excellent | Excellent |
| **Embedding Dim** | 384 | 768 | 1536 |
| **Setup** | Complex | Simple | Simple |
| **Privacy** | Full control | Cloud | Cloud |
| **Scalability** | Limited by hardware | High | High |
| **Offline** | Yes | No | No |

### Cost Estimates (as of Dec 2024)

**Gemini**:
- Vision API: $0.00025 per image
- Embedding API: $0.00001 per 1K characters
- Example: 100 PDFs (10 pages each) = ~$0.25

**OpenAI**:
- GPT-4 Vision: $0.01 per image
- Embeddings: $0.00002 per 1K tokens
- Example: 100 PDFs (10 pages each) = ~$10

**Local Brain**:
- Free (hardware costs only)
- Requires GPU with 8GB+ VRAM

---

## Rollback Plan

If migration fails, rollback to local provider:

```bash
# 1. Update .env
AI_PROVIDER=local

# 2. Restart backend
# Backend will automatically use local provider

# 3. If needed, restore database backup
psql -U postgres -d your_database < backup.sql
```

---

## Testing Migration

### Test Provider Switching

```python
# test_provider_migration.py
import pytest
from services.ai_provider_factory import AIProviderFactory
from config import settings

@pytest.mark.asyncio
async def test_local_provider():
    settings.AI_PROVIDER = "local"
    provider = AIProviderFactory.create_provider()
    
    # Test health check
    is_healthy = await provider.health_check()
    assert is_healthy
    
    # Test embedding dimension
    assert provider.embedding_dimension == 384

@pytest.mark.asyncio
async def test_gemini_provider():
    settings.AI_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = "test-key"
    provider = AIProviderFactory.create_provider()
    
    assert provider.embedding_dimension == 768

@pytest.mark.asyncio
async def test_provider_switching():
    # Test switching between providers
    settings.AI_PROVIDER = "local"
    provider1 = AIProviderFactory.create_provider()
    
    settings.AI_PROVIDER = "gemini"
    provider2 = AIProviderFactory.create_provider()
    
    assert type(provider1) != type(provider2)
```

### Test Embedding Compatibility

```python
# test_embedding_compatibility.py
import pytest

@pytest.mark.asyncio
async def test_embedding_dimensions():
    """Test that embeddings have correct dimensions"""
    providers = [
        ("local", 384),
        ("gemini", 768),
        ("openai", 1536)
    ]
    
    for provider_name, expected_dim in providers:
        settings.AI_PROVIDER = provider_name
        provider = AIProviderFactory.create_provider()
        
        embedding = await provider.generate_embedding("test text")
        assert len(embedding) == expected_dim
```

---

## Future Enhancements

### 1. Hybrid Processing

Use multiple providers for different tasks:

```python
# Use Gemini for OCR (fast, cheap)
# Use OpenAI for embeddings (high quality)

class HybridProvider(AIProvider):
    def __init__(self):
        self.ocr_provider = GeminiProvider(settings.GEMINI_API_KEY)
        self.embedding_provider = OpenAIProvider(settings.OPENAI_API_KEY)
    
    async def extract_text(self, file_data: bytes, filename: str) -> str:
        return await self.ocr_provider.extract_text(file_data, filename)
    
    async def generate_embedding(self, text: str) -> List[float]:
        return await self.embedding_provider.generate_embedding(text)
```

### 2. Batch Processing

Process multiple materials in parallel:

```python
async def batch_process_materials(material_ids: List[str]):
    """Process multiple materials concurrently"""
    tasks = [process_material(mid) for mid in material_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 3. Progress Tracking

Real-time progress updates via WebSocket:

```python
from fastapi import WebSocket

@router.websocket("/ws/materials/{material_id}/progress")
async def material_progress(websocket: WebSocket, material_id: str):
    await websocket.accept()
    
    # Send progress updates
    await websocket.send_json({"status": "processing", "progress": 0})
    # ... OCR processing ...
    await websocket.send_json({"status": "processing", "progress": 50})
    # ... Embedding generation ...
    await websocket.send_json({"status": "completed", "progress": 100})
```

### 4. Re-ranking

Improve search results with re-ranking:

```python
async def search_with_reranking(course_id: str, query: str, limit: int = 3):
    """Search with re-ranking for better results"""
    # Get initial results (top 10)
    initial_results = await search_materials(course_id, query, limit=10)
    
    # Re-rank using cross-encoder
    reranked = await rerank_results(query, initial_results)
    
    # Return top N
    return reranked[:limit]
```

### 5. Citation Tracking

Track which materials were used in responses:

```python
class ChatResponseWithCitations(BaseModel):
    response: str
    timestamp: str
    citations: List[MaterialCitation]

class MaterialCitation(BaseModel):
    material_id: str
    material_name: str
    relevance_score: float
    excerpt_used: str
```

---

## Support

For migration assistance:
- Review design document: `.kiro/specs/material-ocr-embedding/design.md`
- Check configuration guide: `CONFIGURATION_GUIDE.md`
- Test with: `pytest python-backend/test_*.py -v`

---

*Last Updated: December 2024*
