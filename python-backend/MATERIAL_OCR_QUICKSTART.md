# Material OCR & Embedding - Quick Start Guide

Get up and running with material OCR and semantic search in 5 minutes.

## Prerequisites

- PostgreSQL with pgvector extension
- Python 3.8+
- Ollama installed
- AI Brain service set up

## Step 1: Database Setup (2 minutes)

Run these SQL commands in your Supabase SQL editor:

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Add columns to materials table
ALTER TABLE materials 
ADD COLUMN extracted_text TEXT,
ADD COLUMN embedding VECTOR(384),
ADD COLUMN processing_status TEXT DEFAULT 'pending' 
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
ADD COLUMN processed_at TIMESTAMPTZ,
ADD COLUMN error_message TEXT;

-- Create indexes
CREATE INDEX idx_materials_processing_status ON materials(processing_status);
CREATE INDEX idx_materials_embedding ON materials USING hnsw (embedding vector_cosine_ops);

-- Create search function
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

## Step 2: Configure Environment (1 minute)

Add to your `.env` file:

```bash
# AI Brain Service
AI_BRAIN_ENDPOINT=http://localhost:8001
AI_BRAIN_TIMEOUT=300

# Processing
MATERIAL_PROCESSING_TIMEOUT=300
SEARCH_RESULT_LIMIT=3
```

## Step 3: Start Services (1 minute)

### Terminal 1: Start AI Brain

```bash
cd ai-brain
source venv/bin/activate  # Windows: venv\Scripts\activate
python brain.py
```

Wait for: `INFO: Application startup complete.`

### Terminal 2: Start Backend

```bash
cd python-backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload
```

Wait for: `AI Brain service connection verified`

## Step 4: Test Upload (1 minute)

```bash
# Upload a test file
curl -X POST "http://localhost:8000/api/courses/{COURSE_ID}/materials" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test.pdf"

# Response includes material_id
# {
#   "id": "abc-123",
#   "processing_status": "pending",
#   ...
# }
```

## Step 5: Check Status

```bash
# Check processing status
curl -X GET "http://localhost:8000/api/materials/{MATERIAL_ID}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Wait for processing_status: "completed"
```

## Step 6: Search Materials

```bash
# Semantic search
curl -X GET "http://localhost:8000/api/courses/{COURSE_ID}/materials/search?query=machine%20learning" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Returns ranked results with similarity scores
```

## Step 7: Chat with RAG

```bash
# Chat with course context
curl -X POST "http://localhost:8000/api/courses/{COURSE_ID}/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is supervised learning?",
    "history": [],
    "attachments": []
  }'

# AI response includes context from your materials
```

## Verification Checklist

- [ ] pgvector extension enabled
- [ ] Materials table has new columns
- [ ] Indexes created successfully
- [ ] AI Brain service running on port 8001
- [ ] Backend running on port 8000
- [ ] Backend logs show "AI Brain service connection verified"
- [ ] Test file uploaded successfully
- [ ] Material status changed to "completed"
- [ ] Search returns relevant results
- [ ] Chat includes material context

## Troubleshooting

### AI Brain not connecting
```bash
# Check if service is running
curl http://localhost:8001/

# Should return: {"status": "ok"}
```

### Materials stuck in "pending"
- Check AI Brain service is running
- Check backend logs for errors
- Verify AI_BRAIN_ENDPOINT in .env

### Search returns empty
- Verify materials have `processing_status: "completed"`
- Check materials have `has_embedding: true`
- Try broader search queries

### Processing timeout
- Increase timeout in .env: `AI_BRAIN_TIMEOUT=600`
- Restart backend
- Re-upload material

## Next Steps

- Read full guide: `MATERIAL_OCR_EMBEDDING_GUIDE.md`
- Review API documentation
- Run tests: `pytest python-backend/ -v`
- Integrate with frontend

## Common API Endpoints

```bash
# Upload
POST /api/courses/{course_id}/materials

# List materials
GET /api/courses/{course_id}/materials

# Get material details
GET /api/materials/{material_id}

# Search
GET /api/courses/{course_id}/materials/search?query={query}&limit={limit}

# Chat with RAG
POST /api/courses/{course_id}/chat

# Download
GET /api/materials/{material_id}/download

# Delete
DELETE /api/materials/{material_id}
```

## Support

For detailed documentation, see:
- `MATERIAL_OCR_EMBEDDING_GUIDE.md` - Complete guide
- `.kiro/specs/material-ocr-embedding/design.md` - Technical design
- `.kiro/specs/material-ocr-embedding/requirements.md` - Requirements

---

**Ready to go!** Upload your first material and start searching. 🚀
