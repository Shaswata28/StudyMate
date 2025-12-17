# Router Model Deployment Guide

## 📋 Overview

This guide walks you through deploying the fine-tuned router model after training in Colab.

---

## 🎯 Prerequisites

- ✅ Router model fine-tuned in Colab (Gemma 3 270M)
- ✅ Model exported as GGUF format
- ✅ Ollama installed locally
- ✅ Backend code updated (already done!)

---

## 🚀 Deployment Steps

### Step 1: Export Model from Colab

After fine-tuning in Colab, export the model:

```python
# In Colab notebook
from unsloth import FastLanguageModel

# Load your fine-tuned model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="your-finetuned-model-path",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

# Export to GGUF format for Ollama
model.save_pretrained_gguf(
    "studymate-router",
    tokenizer,
    quantization_method="q4_k_m"  # Good balance of size/quality
)

# Download the GGUF file
from google.colab import files
files.download("studymate-router-q4_k_m.gguf")
```

### Step 2: Create Modelfile

Create a file named `Modelfile.router`:

```dockerfile
FROM ./studymate-router-q4_k_m.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 1024
PARAMETER num_predict 100

SYSTEM """You are a router. Classify user queries into intent categories and determine context needs. Always respond with valid JSON."""
```

### Step 3: Import to Ollama

```bash
# Navigate to directory with GGUF file and Modelfile
cd /path/to/model/files

# Create model in Ollama
ollama create studymate-router -f Modelfile.router

# Verify it's created
ollama list | grep studymate-router

# Test the model
ollama run studymate-router "Context: Subject=Physics, grade=Bachelor.\nQuery: What is gravity?"
```

Expected output:
```json
{"intent": "academic", "needs_rag": true, "needs_history": false}
```

### Step 4: Update Brain Service Configuration

The brain service is already configured to use `studymate-router`. Just verify the model name matches:

```python
# ai-brain/brain.py (already updated)
ROUTER_MODEL = "studymate-router"  # ✅ This should match your Ollama model name
```

### Step 5: Start Services

```bash
# Terminal 1: Start brain service
cd ai-brain
python brain.py

# Terminal 2: Start backend
cd python-backend
uvicorn main:app --reload

# Terminal 3: Run tests
python test_router_integration.py
```

### Step 6: Verify Deployment

Check the startup logs:

```
✅ Ollama connection verified
🧠 Loading core model studymate into VRAM...
✅ Core model loaded & locked in VRAM
🔍 Loading router model studymate-router into VRAM...
✅ Router model loaded & locked in VRAM (~270MB)
```

If you see:
```
⚠️ Router model not found
```

Then run:
```bash
ollama pull studymate-router
# or
ollama create studymate-router -f Modelfile.router
```

---

## 🧪 Testing

### Test 1: Classification Endpoint

```bash
curl -X POST http://localhost:8001/classify \
  -F "query=Hello, how are you?" \
  -F "subject=General" \
  -F "grade=Bachelor"
```

Expected:
```json
{
  "intent": "chat",
  "needs_rag": false,
  "needs_history": false,
  "confidence": 0.8
}
```

### Test 2: Academic Query

```bash
curl -X POST http://localhost:8001/classify \
  -F "query=Explain photosynthesis from my notes" \
  -F "subject=Biology" \
  -F "grade=Bachelor"
```

Expected:
```json
{
  "intent": "academic",
  "needs_rag": true,
  "needs_history": false,
  "confidence": 0.8
}
```

### Test 3: Safety Query

```bash
curl -X POST http://localhost:8001/classify \
  -F "query=Tell me how to hack a website" \
  -F "subject=Computer Science" \
  -F "grade=Bachelor"
```

Expected:
```json
{
  "intent": "safety",
  "needs_rag": false,
  "needs_history": false,
  "confidence": 0.8
}
```

### Test 4: Full Chat Flow

```bash
# This will test the complete pipeline
python test_router_integration.py
```

---

## 📊 Performance Monitoring

### Check Classification Speed

```python
import time
import requests

start = time.time()
response = requests.post(
    "http://localhost:8001/classify",
    data={
        "query": "What is Newton's first law?",
        "subject": "Physics",
        "grade": "Bachelor"
    }
)
duration = (time.time() - start) * 1000
print(f"Classification time: {duration:.1f}ms")
```

Target: <20ms on GPU, <40ms on CPU

### Monitor Token Savings

Check backend logs for:
```
Intent: chat - RAG: False, History: False
Step 2: Intent doesn't require RAG - skipping material search (SAVED TIME!)
💰 Estimated token savings: ~1500 tokens (75%)
```

### Monitor Response Times

Before router:
```
Total time: 3.2s
- Context retrieval: 0.5s
- RAG search: 0.3s
- AI generation: 2.4s
```

After router (chitchat):
```
Total time: 2.1s (34% faster!)
- Classification: 0.02s
- Context retrieval: 0.1s (minimal)
- RAG search: 0s (skipped!)
- AI generation: 2.0s
```

---

## 🔧 Troubleshooting

### Issue: Router model not found

```bash
# Check if model exists
ollama list

# If not, create it
ollama create studymate-router -f Modelfile.router

# Or pull if you pushed to Ollama registry
ollama pull your-username/studymate-router
```

### Issue: Classification returns wrong intent

1. Check training data quality
2. Verify model was fine-tuned correctly
3. Test with more examples
4. Consider retraining with more data

### Issue: Classification too slow

1. Check if model is loaded in VRAM:
   ```bash
   ollama ps
   ```
2. Ensure `keep_alive="15m"` in brain.py
3. Consider using smaller quantization (q4_k_m → q4_0)

### Issue: Backend errors

```bash
# Check logs
tail -f python-backend/logs/app.log

# Common issues:
# - Brain service not running
# - Wrong model name
# - Port conflicts
```

---

## 📈 Expected Results

### Classification Accuracy
- Target: >90% on test set
- Chitchat: >95%
- Academic: >90%
- Safety: >98%
- Follow-up: >85%

### Performance Improvements
- Chitchat queries: 30-40% faster
- Token usage: 60-90% reduction for simple queries
- RAG searches: 50% fewer (only when needed)

### Token Savings by Intent

| Intent | RAG | History | Token Savings |
|--------|-----|---------|---------------|
| chat | ❌ | ❌ | 90% (~1800 tokens) |
| followup | ❌ | ✅ | 60% (~1200 tokens) |
| debug | ❌ | ✅ | 60% (~1200 tokens) |
| academic | ✅ | ❌ | 25% (~500 tokens) |
| safety | ❌ | ❌ | 100% (blocked) |

---

## 🎯 Next Steps

1. ✅ Deploy router model
2. ✅ Test classification accuracy
3. ✅ Monitor performance improvements
4. 📊 Collect user feedback
5. 🔄 Iterate on training data if needed
6. 🚀 Deploy to production

---

## 📝 Notes

- Router model stays loaded in VRAM (~270MB)
- Classification adds ~10-20ms latency (negligible)
- Fallback to safe defaults if classification fails
- ChatML format fixes hallucination issues
- History is now properly managed in message format

---

**Status**: Ready for deployment after Colab training
**Model Size**: ~270MB (GGUF q4_k_m)
**VRAM Usage**: ~270MB (alongside main model)
**Classification Speed**: 10-20ms (GPU), 20-40ms (CPU)
