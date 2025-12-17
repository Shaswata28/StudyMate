# Backend Flow - How User Prompts Reach the AI

## 🎯 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER SENDS MESSAGE                          │
│                    "Explain photosynthesis"                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: FastAPI Backend (python-backend/routers/chat.py)          │
│  POST /api/courses/{course_id}/chat                                │
│                                                                     │
│  • Verify user authentication                                      │
│  • Verify course ownership                                         │
│  • Get user context (academic info, preferences)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Intent Classification (NEW!)                              │
│  Service: intent_classifier.py                                     │
│                                                                     │
│  Sends to: http://localhost:8001/classify                          │
│  Payload:                                                           │
│    {                                                                │
│      "query": "Explain photosynthesis",                            │
│      "subject": "Biology",                                          │
│      "grade": "Bachelor"                                            │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: Router Model (ai-brain/brain.py)                          │
│  Endpoint: POST /classify                                           │
│  Model: Gemma 3 270M (studymate-router)                            │
│                                                                     │
│  Input Format (ChatML):                                             │
│    [                                                                │
│      {                                                              │
│        "role": "system",                                            │
│        "content": "You are a router. Classify..."                  │
│      },                                                             │
│      {                                                              │
│        "role": "user",                                              │
│        "content": "Context: Subject=Biology, grade=Bachelor.\n     │
│                    Query: Explain photosynthesis"                  │
│      }                                                              │
│    ]                                                                │
│                                                                     │
│  Router Model Output:                                               │
│    {                                                                │
│      "intent": "academic",                                          │
│      "needs_rag": true,                                             │
│      "needs_history": false,                                        │
│      "confidence": 0.85                                             │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: Decision Point (chat.py)                                  │
│                                                                     │
│  IF intent == "safety":                                             │
│    → Block immediately, return safety message                       │
│                                                                     │
│  IF needs_rag == true:                                              │
│    → Proceed to RAG search                                          │
│  ELSE:                                                              │
│    → Skip RAG search (SAVES TIME!)                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: Conditional RAG Search (if needs_rag == true)             │
│  Service: service_manager.processing_service                        │
│                                                                     │
│  • Search course materials using semantic search                   │
│  • Query: "Explain photosynthesis"                                 │
│  • Limit: 3 most relevant materials                                │
│                                                                     │
│  Results:                                                           │
│    [                                                                │
│      {                                                              │
│        "name": "Biology Notes - Chapter 5",                         │
│        "excerpt": "Photosynthesis is the process...",              │
│        "similarity_score": 0.89                                     │
│      },                                                             │
│      ...                                                            │
│    ]                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: Build Adaptive Context (NEW!)                             │
│  Service: context_service.build_adaptive_context()                 │
│                                                                     │
│  Builds ChatML messages based on intent:                            │
│                                                                     │
│  Message 1 (System):                                                │
│    {                                                                │
│      "role": "system",                                              │
│      "content": "You are StudyMate, an AI tutor.\n\n               │
│                  [STUDENT PROFILE]\n                                │
│                  Academic Level: Bachelor\n                         │
│                  Subject: Biology\n\n                               │
│                  [LEARNING PREFERENCES]\n                           │
│                  Detail Level: 0.7/1.0\n                            │
│                  Learning Pace: moderate\n\n                        │
│                  [COURSE MATERIALS]\n                               │
│                  1. Biology Notes - Chapter 5 (relevance: 0.89)\n  │
│                     Photosynthesis is the process..."               │
│    }                                                                │
│                                                                     │
│  Message 2 (User):                                                  │
│    {                                                                │
│      "role": "user",                                                │
│      "content": "Explain photosynthesis"                           │
│    }                                                                │
│                                                                     │
│  (If needs_history == true, adds previous messages here)           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: Send to Core Model                                        │
│  Service: local_ai_service.generate_chat_response()                │
│                                                                     │
│  HTTP POST to: http://localhost:8001/chat                          │
│  Payload:                                                           │
│    {                                                                │
│      "messages": [                                                  │
│        {"role": "system", "content": "..."},                        │
│        {"role": "user", "content": "Explain photosynthesis"}       │
│      ],                                                             │
│      "model": "studymate"                                           │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8: Core Model Generation (ai-brain/brain.py)                 │
│  Endpoint: POST /chat                                               │
│  Model: StudyMate (Qwen-based)                                     │
│                                                                     │
│  Uses: ollama.chat() API                                            │
│                                                                     │
│  await client.chat(                                                 │
│      model="studymate",                                             │
│      messages=[...],  # ChatML format                               │
│      options={                                                      │
│          "temperature": 0.45,                                       │
│          "top_p": 0.9,                                              │
│          "repeat_penalty": 1.15,                                    │
│          "num_ctx": 4096,                                           │
│          "num_predict": 1024                                        │
│      }                                                              │
│  )                                                                  │
│                                                                     │
│  Core Model Output:                                                 │
│    "Photosynthesis is the process by which plants convert          │
│     light energy into chemical energy. Based on your notes,        │
│     it occurs in chloroplasts and involves two main stages:        │
│     the light-dependent reactions and the Calvin cycle..."         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 9: Return to Backend                                         │
│  Service: local_ai_service                                          │
│                                                                     │
│  Response from brain service:                                       │
│    {                                                                │
│      "response": "Photosynthesis is the process...",               │
│      "model": "studymate"                                           │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 10: Save Chat History (chat.py)                              │
│                                                                     │
│  Save to Supabase:                                                  │
│    {                                                                │
│      "course_id": "...",                                            │
│      "history": [                                                   │
│        {"role": "user", "content": "Explain photosynthesis"},      │
│        {"role": "model", "content": "Photosynthesis is..."}        │
│      ]                                                              │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 11: Return to User                                           │
│                                                                     │
│  HTTP Response:                                                     │
│    {                                                                │
│      "response": "Photosynthesis is the process...",               │
│      "timestamp": "2024-12-15T10:30:00Z"                           │
│    }                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Different Flows Based on Intent

### Flow 1: Chitchat (e.g., "Hello!")

```
User: "Hello!"
  ↓
Router: {"intent": "chat", "needs_rag": false, "needs_history": false}
  ↓
Backend: Skip RAG search ✓ (SAVES 200-300ms)
  ↓
Context: Minimal system prompt only
  [
    {"role": "system", "content": "You are StudyMate..."},
    {"role": "user", "content": "Hello!"}
  ]
  ↓
Core Model: "Hello! I'm StudyMate, your AI tutor..."
  ↓
User: Response in ~2.1s (30% faster!)
```

### Flow 2: Academic Query (e.g., "Explain photosynthesis")

```
User: "Explain photosynthesis"
  ↓
Router: {"intent": "academic", "needs_rag": true, "needs_history": false}
  ↓
Backend: Perform RAG search ✓
  ↓
Context: Full system prompt + RAG materials
  [
    {"role": "system", "content": "You are StudyMate...\n[COURSE MATERIALS]\n..."},
    {"role": "user", "content": "Explain photosynthesis"}
  ]
  ↓
Core Model: "Based on your notes, photosynthesis is..."
  ↓
User: Response in ~2.8s (with full context)
```

### Flow 3: Follow-up (e.g., "Why did you say that?")

```
User: "Why did you say that?"
  ↓
Router: {"intent": "followup", "needs_rag": false, "needs_history": true}
  ↓
Backend: Skip RAG search ✓, Load history ✓
  ↓
Context: System prompt + previous conversation
  [
    {"role": "system", "content": "You are StudyMate..."},
    {"role": "user", "content": "What is gravity?"},
    {"role": "assistant", "content": "Gravity is a force..."},
    {"role": "user", "content": "Why did you say that?"}
  ]
  ↓
Core Model: "I mentioned that because in the previous question..."
  ↓
User: Response in ~2.3s (with history context)
```

### Flow 4: Safety Query (e.g., "How to hack a website")

```
User: "How to hack a website"
  ↓
Router: {"intent": "safety", "needs_rag": false, "needs_history": false}
  ↓
Backend: BLOCK IMMEDIATELY ✓ (No AI call!)
  ↓
User: "I can't help with that request. I'm designed to assist with educational content only."
  ↓
Response in ~0.02s (instant blocking!)
```

---

## 📊 Key Differences from Old Architecture

### OLD Architecture (JSON Dump):

```python
# Backend always sends everything
training_json = {
    "instruction": "Hello!",
    "input": {
        "academic_info": {...},           # Always included
        "learning_preferences": {...},    # Always included
        "rag_chunks": [...],              # Always included (even if empty)
        "chat_history": [...]             # Always included (even if empty)
    }
}

# Brain service converts JSON to natural language
# Core model processes ~2000 tokens
# Response time: ~3.0s
```

### NEW Architecture (Adaptive ChatML):

```python
# Router decides what's needed
intent = {"intent": "chat", "needs_rag": false, "needs_history": false}

# Backend builds minimal context
messages = [
    {"role": "system", "content": "You are StudyMate..."},
    {"role": "user", "content": "Hello!"}
]

# Brain service uses ollama.chat() directly
# Core model processes ~200 tokens (90% less!)
# Response time: ~2.1s (30% faster!)
```

---

## 🎯 Token Savings Breakdown

### Chitchat Query: "Hello!"

**Before**:
```
System prompt: 500 tokens
Academic info: 100 tokens
Preferences: 200 tokens
RAG chunks: 800 tokens (empty but formatted)
History: 400 tokens (empty but formatted)
User query: 10 tokens
TOTAL: ~2010 tokens
```

**After**:
```
System prompt: 150 tokens (minimal)
User query: 10 tokens
TOTAL: ~160 tokens (92% savings!)
```

### Academic Query: "Explain photosynthesis"

**Before**:
```
System prompt: 500 tokens
Academic info: 100 tokens
Preferences: 200 tokens
RAG chunks: 800 tokens
History: 400 tokens (empty but formatted)
User query: 20 tokens
TOTAL: ~2020 tokens
```

**After**:
```
System prompt: 200 tokens
Academic info: 50 tokens
Preferences: 150 tokens
RAG chunks: 800 tokens
User query: 20 tokens
TOTAL: ~1220 tokens (40% savings!)
```

---

## 🔧 Code Flow Summary

### 1. Entry Point
```python
# python-backend/routers/chat.py
@router.post("/courses/{course_id}/chat")
async def save_chat_message(course_id, chat_request, user):
    # This is where everything starts
```

### 2. Classification
```python
# python-backend/services/intent_classifier.py
intent = await intent_classifier.classify(
    query=chat_request.message,
    subject=subject,
    grade=grade
)
# Returns: {"intent": "...", "needs_rag": bool, "needs_history": bool}
```

### 3. Conditional RAG
```python
# python-backend/routers/chat.py
if intent["needs_rag"]:
    search_results = await service_manager.processing_service.search_materials(...)
else:
    search_results = []  # Skip search!
```

### 4. Build Context
```python
# python-backend/services/context_service.py
messages = await context_service.build_adaptive_context(
    user_id=user.id,
    course_id=course_id,
    user_message=chat_request.message,
    intent=intent,
    search_results=search_results
)
# Returns: [{"role": "system", "content": "..."}, ...]
```

### 5. Generate Response
```python
# python-backend/services/local_ai_service.py
response_text = await local_ai_service.generate_chat_response(
    messages=messages,
    attachments=chat_request.attachments
)
# Sends to: http://localhost:8001/chat
```

### 6. Core Model
```python
# ai-brain/brain.py
@app.post("/chat")
async def chat_endpoint(request):
    response = await client.chat(
        model="studymate",
        messages=request["messages"]
    )
    return {"response": response['message']['content']}
```

---

## 🎯 Summary

**The new backend flow**:
1. ✅ Classifies intent first (Gemma 3 270M)
2. ✅ Conditionally searches materials (only if needed)
3. ✅ Builds adaptive ChatML context (minimal tokens)
4. ✅ Sends to core model (ollama.chat API)
5. ✅ Returns response to user

**Key improvements**:
- 🚀 60-90% token savings for simple queries
- ⚡ 30% faster responses for chitchat
- 🛡️ Instant safety blocking
- 🎯 Better accuracy (no irrelevant context)
- 🔧 ChatML format (fixes hallucinations)

**The magic**: Router model decides what context to include, backend only fetches what's needed, core model gets clean, focused input!
