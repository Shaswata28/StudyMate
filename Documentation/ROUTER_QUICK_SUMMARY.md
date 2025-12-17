# Router Implementation - Quick Summary

## 🎯 What We're Building

**Smart Router System**: Use a tiny fine-tuned model (Gemma 3 270M) to classify queries and send only relevant context to your main StudyMate model.

---

## 📊 Your Datasets

### Router Dataset (`dataset_router/`) - 800+ examples
Trains Gemma 3 270M to classify queries:

| File | Purpose | Example Output |
|------|---------|----------------|
| `academic.jsonl` | Study questions | `{"intent": "academic", "needs_rag": true, "needs_history": false}` |
| `chitchat.jsonl` | Casual chat | `{"intent": "chat", "needs_rag": false, "needs_history": false}` |
| `contextual.jsonl` | Follow-ups | `{"intent": "followup", "needs_rag": false, "needs_history": true}` |
| `debugging.jsonl` | Code help | `{"intent": "debug", "needs_rag": false, "needs_history": true}` |
| `safety.jsonl` | Harmful queries | `{"intent": "safety", "needs_rag": false, "needs_history": false}` |

### Core Dataset (`dataset_core/`) - 599 examples
Trains your main StudyMate model for educational responses.

---

## 🏗️ Architecture Flow

```
User: "Hello!"
    ↓
Router (Gemma 3 270M): {"intent": "chat", "needs_rag": false}
    ↓
Backend: Skip RAG search, minimal context
    ↓
Core Model: Fast response (~2s vs 3s)
```

```
User: "Explain photosynthesis from my notes"
    ↓
Router (Gemma 3 270M): {"intent": "academic", "needs_rag": true}
    ↓
Backend: Search materials, add preferences
    ↓
Core Model: Full context response
```

---

## 💡 Key Benefits

1. **Token Savings**: 60-90% reduction for simple queries
2. **Faster Responses**: 15-30% speed improvement
3. **Better Accuracy**: Model gets only relevant context
4. **Safety**: Blocks harmful queries immediately
5. **ChatML Format**: Aligns with Qwen training (fixes hallucinations)

---

## 🔧 Implementation Steps

### 1. Fine-tune Router Model
```bash
# Combine router datasets
cd Dataset/dataset_router
cat *.jsonl > combined_router.jsonl

# Fine-tune Gemma 3 270M
ollama create studymate-router -f Modelfile.router
```

### 2. Add Classification Endpoint
```python
# ai-brain/brain.py
@app.post("/classify")
async def classify_query(query, subject, grade):
    # Use fine-tuned Gemma 3 270M
    response = await client.chat(
        model="studymate-router",
        messages=[...]
    )
    return {"intent": "...", "needs_rag": bool, "needs_history": bool}
```

### 3. Update Backend
```python
# python-backend/routers/chat.py
# 1. Classify intent
intent = await intent_classifier.classify(query)

# 2. Conditionally search materials
if intent["needs_rag"]:
    search_results = await search_materials(...)

# 3. Build adaptive context (ChatML format)
messages = await build_adaptive_context(intent, search_results)

# 4. Generate response
response = await core_model.chat(messages)
```

### 4. Switch to ChatML Format
```python
# Old: JSON dump
{"instruction": "...", "input": {...}}

# New: ChatML messages
[
    {"role": "system", "content": "You are StudyMate...\n[COURSE MATERIALS]\n..."},
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"},
    {"role": "user", "content": "current question"}
]
```

---

## 📈 Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Chitchat latency | 3.0s | 2.1s | 30% faster |
| Token usage (chitchat) | 2000 | 200 | 90% less |
| Token usage (study) | 2000 | 1500 | 25% less |
| Hallucinations | Occasional | Rare | Better |
| Safety blocking | Manual | Automatic | Instant |

---

## ✅ Next Steps

1. **Review** `ROUTER_IMPLEMENTATION_PLAN.md` for detailed code
2. **Fine-tune** Gemma 3 270M with your router dataset
3. **Test** classification accuracy
4. **Implement** backend changes
5. **Deploy** and monitor

---

## 🎯 Why This Works

1. **Gemma 3 270M** is perfect for classification (tiny, fast, accurate)
2. **Your datasets** are well-structured and comprehensive
3. **ChatML format** matches how Qwen models are trained
4. **Adaptive context** reduces noise and improves accuracy
5. **Fallback defaults** ensure reliability

---

**Ready to implement?** Check `ROUTER_IMPLEMENTATION_PLAN.md` for step-by-step code!
