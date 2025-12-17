# RAG System Verification Guide

This guide helps you verify that your AI is actually using the RAG (Retrieval-Augmented Generation) system.

## Quick Overview

Your RAG system works in these steps:
1. User asks a question
2. System searches for relevant materials using embeddings (1024-dim vectors)
3. Top results are formatted as "rag_chunks" in the prompt
4. AI receives the chunks and should use them in the response

## Test Files Created

### 1. `quick_rag_check.py` - Start Here! ⭐
**What it does:** Checks if RAG chunks are properly formatted in prompts
**No services needed:** Runs offline, just checks formatting logic
**Run:** `python quick_rag_check.py`

This will show you:
- How prompts look WITHOUT RAG
- How prompts look WITH RAG
- What the AI actually receives

### 2. `test_rag_live.py` - Live API Test
**What it does:** Tests with actual API calls to your AI Brain
**Requires:** AI Brain service running on port 8001
**Run:** `python test_rag_live.py`

This will:
- Send a prompt WITHOUT RAG chunks
- Send a prompt WITH RAG chunks containing unique info
- Compare responses to see if AI used the RAG data

### 3. `test_rag_verification.py` - Full Integration Test
**What it does:** Comprehensive test with material upload and search
**Requires:** Full backend + AI Brain running
**Run:** `python test_rag_verification.py`

## How to Verify RAG is Working

### Step 1: Check Formatting (Offline)
```bash
python quick_rag_check.py
```

**Expected output:**
- ✅ RAG chunks in JSON: True
- ✅ RAG context in final prompt: True
- ✅ Actual content present: True

If this fails, your `context_service.py` or `brain.py` has formatting issues.

### Step 2: Test Live (Requires AI Brain)
```bash
# Start AI Brain first
cd ai-brain
python brain.py

# In another terminal
python test_rag_live.py
```

**What to look for:**
- The AI should mention "0.847" (the Zephyr Coefficient from RAG chunks)
- If it does: ✅ RAG is working!
- If it doesn't: ❌ AI is not using RAG chunks

### Step 3: Check Your Logs

When RAG is working, you should see these logs:

**In context_service.py:**
```
INFO: Added 3 RAG chunks to training JSON
INFO: Generated training JSON structure with 3 RAG chunks
```

**In brain.py:**
```
INFO: Received training JSON - converting to natural prompt
INFO: Built natural prompt from JSON (XXX chars)
```

**In material_processing_service.py:**
```
INFO: Query embedding generated in X.XXs (1024 dimensions)
INFO: Found X relevant materials for query
```

## Common Issues

### Issue 1: AI doesn't use RAG chunks
**Symptoms:** AI gives generic answers, doesn't mention specific info from materials

**Check:**
1. Is `brain.py` parsing the JSON correctly?
   - Look for: `if isinstance(data, dict) and "instruction" in data`
2. Are RAG chunks being extracted?
   - Look for: `rag_chunks = input_data.get("rag_chunks", [])`
3. Is the natural prompt being built?
   - Look for: `context_parts.append("Relevant course materials:")`

**Fix:** Check the JSON parsing logic in `brain.py` around line 200-250

### Issue 2: No RAG chunks in prompt
**Symptoms:** `len(rag_chunks) = 0` in logs

**Check:**
1. Is material search working?
   - Test: `python -m pytest Testing/python-backend/test_search_endpoint.py`
2. Are materials processed with embeddings?
   - Check database: Materials should have non-null `embedding` column
3. Is context service calling search?
   - Check `routers/chat.py` - should call `processing_service.search_materials()`

**Fix:** Verify material processing and search pipeline

### Issue 3: Wrong embedding dimensions
**Symptoms:** Errors about vector dimensions

**Current setup:**
- Embedding model: `mxbai-embed-large` (1024 dimensions)
- Database: Should be configured for 1024-dim vectors
- Constants.py: Shows 384 (OUTDATED!)

**Fix:** Update `python-backend/constants.py`:
```python
EMBEDDING_DIMENSION = 1024  # Changed from 384
```

## Manual Testing via API

You can also test manually using curl:

```bash
# Test WITH RAG chunks
curl -X POST http://localhost:8001/router \
  -F 'prompt={
    "instruction": "What is quantum computing?",
    "input": {
      "rag_chunks": [
        {
          "name": "Quantum Physics 101",
          "excerpt": "Quantum computing uses qubits...",
          "similarity_score": 0.95
        }
      ]
    }
  }'
```

## Debugging Checklist

- [ ] AI Brain service is running (port 8001)
- [ ] Backend service is running (port 8000)
- [ ] Materials are uploaded and processed
- [ ] Materials have embeddings (check database)
- [ ] Search returns results (test search endpoint)
- [ ] Context service includes search results
- [ ] brain.py receives JSON with rag_chunks
- [ ] brain.py parses JSON correctly
- [ ] Final prompt includes "Relevant course materials:"
- [ ] AI response uses information from materials

## Expected Flow

```
User Question
    ↓
Search Materials (using embedding similarity)
    ↓
Top 3 Results → rag_chunks
    ↓
Context Service formats training JSON
    ↓
{
  "instruction": "user question",
  "input": {
    "rag_chunks": [...],  ← Should have 3 items
    ...
  }
}
    ↓
brain.py receives JSON
    ↓
Parses and builds natural prompt:
"Relevant course materials:
1. Material Name (relevance: 0.95)
   excerpt...

Question: user question"
    ↓
Ollama generates response using context
    ↓
Response should reference the materials
```

## Success Criteria

✅ RAG is working if:
1. Search returns relevant materials
2. Materials appear in rag_chunks
3. brain.py builds prompt with "Relevant course materials:"
4. AI response contains specific info from the materials
5. AI can answer questions it couldn't answer without RAG

## Next Steps

After verifying RAG works:
1. Test with real course materials
2. Monitor response quality
3. Adjust similarity thresholds if needed
4. Fine-tune the number of chunks (currently 3)
5. Optimize excerpt length for better context
