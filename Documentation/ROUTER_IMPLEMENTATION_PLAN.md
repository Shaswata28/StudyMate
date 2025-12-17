# Router Model Implementation Plan

## 📋 Overview

Transform the backend architecture to use a **fine-tuned router model (Gemma 3 270M)** that intelligently classifies user queries and dynamically constructs context for the core model.

---

## 🎯 Architecture Goals

### Current Problem:
- Backend dumps ALL context (RAG + preferences + history) to the model
- Causes token bloat, slower responses, and potential hallucinations
- Model receives irrelevant information for simple queries

### Solution:
- **Router Model**: Gemma 3 270M fine-tuned on `dataset_router/`
- **Core Model**: StudyMate (Qwen-based) fine-tuned on `dataset_core/`
- **Smart Context**: Router decides what context to send

---

## 📊 Dataset Analysis

### Router Dataset (`dataset_router/`)
**Purpose**: Train Gemma 3 270M to classify queries and determine context needs

**Files**:
1. `academic.jsonl` (321 lines) - Academic questions needing RAG
2. `chitchat.jsonl` (161 lines) - Casual conversation, no RAG needed
3. `contextual.jsonl` (161 lines) - Follow-up questions needing history
4. `debugging.jsonl` - Code debugging, needs history
5. `safety.jsonl` - Harmful queries to reject
6. `tricky.jsonl` - Edge cases

**Format**:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a router. Classify the user query based on the context into JSON: 'intent' (academic, chat, debug, followup, safety), 'needs_rag' (true/false), 'needs_history' (true/false)."
    },
    {
      "role": "user",
      "content": "Context: Subject=Physics, grade=Masters.\nQuery: What are Newton's three laws of motion?"
    },
    {
      "role": "assistant",
      "content": "{\"intent\": \"academic\", \"needs_rag\": true, \"needs_history\": false}"
    }
  ]
}
```

**Intent Categories**:
- `academic`: Study questions → needs RAG + preferences
- `chat`: Casual conversation → needs nothing or minimal history
- `debug`: Code debugging → needs history (for code context)
- `followup`: Contextual questions → needs history
- `safety`: Harmful queries → reject immediately

### Core Dataset (`dataset_core/`)
**Purpose**: Train StudyMate core model for educational responses

**Files**:
1. `Context_Rich_Tutor.jsonl` - RAG-enhanced tutoring
2. `Debugger.jsonl` - Code debugging assistance
3. `Follow-up.jsonl` - Contextual follow-ups
4. `MultiTurnDebugger.jsonl` - Multi-turn debugging
5. `Pure_Chat.jsonl` - Casual conversation
6. `Safety&Guardrails.jsonl` - Safety responses
7. `Visualizer.jsonl` - Visual explanations

---

## 🏗️ Implementation Architecture

```
User Query
    ↓
┌─────────────────────────────────────────┐
│  1. Intent Classification               │
│     (Gemma 3 270M Router)               │
│     - Classify intent                   │
│     - Determine context needs           │
│     Output: {intent, needs_rag,         │
│              needs_history}             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  2. Conditional Context Building        │
│     (context_service.py)                │
│     - IF needs_rag → search materials   │
│     - IF needs_history → fetch history  │
│     - Always include preferences        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  3. Prompt Construction                 │
│     (ChatML format)                     │
│     - System prompt with context        │
│     - History messages (if needed)      │
│     - Current user query                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  4. Core Model Generation               │
│     (StudyMate - Qwen-based)            │
│     - Generate response                 │
│     - Use ollama.chat() API             │
└─────────────────────────────────────────┘
    ↓
Response to User
```

---

## 🔧 Implementation Steps

### **Phase 1: Fine-tune Router Model**

#### 1.1 Prepare Router Training Data
```bash
cd Dataset/dataset_router
# Combine all router datasets
cat academic.jsonl chitchat.jsonl contextual.jsonl debugging.jsonl safety.jsonl tricky.jsonl > combined_router.jsonl
```

#### 1.2 Fine-tune Gemma 3 270M
```bash
# Using Ollama's fine-tuning (or Unsloth for faster training)
ollama create studymate-router -f Modelfile.router

# Modelfile.router content:
FROM gemma3:270m
ADAPTER ./router_adapter
PARAMETER temperature 0.1
PARAMETER top_p 0.9
SYSTEM You are a router. Classify user queries into intent categories and determine context needs.
```

#### 1.3 Test Router Model
```python
# test_router.py
import ollama

test_queries = [
    "Hello, how are you?",  # Expected: chat, no RAG
    "Explain photosynthesis",  # Expected: academic, needs RAG
    "Why did you say that?",  # Expected: followup, needs history
]

for query in test_queries:
    response = ollama.chat(
        model="studymate-router",
        messages=[
            {"role": "system", "content": "You are a router..."},
            {"role": "user", "content": f"Context: Subject=Biology, grade=Bachelor.\nQuery: {query}"}
        ]
    )
    print(f"Query: {query}")
    print(f"Classification: {response['message']['content']}\n")
```

---

### **Phase 2: Update Backend Architecture**

#### 2.1 Add Router Endpoint to `brain.py`

```python
# ai-brain/brain.py

CORE_MODEL = "studymate"
ROUTER_MODEL = "studymate-router"  # ← NEW
VISION_MODEL = "qwen2.5vl:3b"
EMBEDDING_MODEL = "mxbai-embed-large"

@app.post("/classify")
async def classify_query(
    query: str = Form(...),
    subject: str = Form("General"),
    grade: str = Form("Bachelor")
):
    """
    Classify user query using fine-tuned Gemma 3 270M router.
    Returns intent and context requirements.
    """
    try:
        context_info = f"Context: Subject={subject}, grade={grade}.\nQuery: {query}"
        
        response = await client.chat(
            model=ROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a router. Classify the user query based on the context into JSON: 'intent' (academic, chat, debug, followup, safety), 'needs_rag' (true/false), 'needs_history' (true/false)."
                },
                {
                    "role": "user",
                    "content": context_info
                }
            ],
            keep_alive="15m",
            options={
                "temperature": 0.1,
                "num_predict": 100
            }
        )
        
        classification_text = response['message']['content'].strip()
        
        # Parse JSON
        json_match = re.search(r'\{[^}]*\}', classification_text)
        if json_match:
            classification = json.loads(json_match.group(0))
        else:
            # Fallback
            classification = {
                "intent": "academic",
                "needs_rag": True,
                "needs_history": True
            }
        
        logger.info(f"Classification: {classification}")
        return classification
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        # Safe default
        return {
            "intent": "academic",
            "needs_rag": True,
            "needs_history": True
        }
```

#### 2.2 Create Intent Classifier Service

```python
# python-backend/services/intent_classifier.py

import logging
import httpx
from typing import Dict

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Service for classifying user query intent using fine-tuned router model.
    """
    
    def __init__(self, brain_url: str = "http://localhost:8001"):
        self.brain_url = brain_url
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def classify(
        self,
        query: str,
        subject: str = "General",
        grade: str = "Bachelor"
    ) -> Dict:
        """
        Classify user query intent.
        
        Returns:
            {
                "intent": "academic" | "chat" | "debug" | "followup" | "safety",
                "needs_rag": bool,
                "needs_history": bool
            }
        """
        try:
            response = await self.client.post(
                f"{self.brain_url}/classify",
                data={
                    "query": query,
                    "subject": subject,
                    "grade": grade
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Classification failed: {response.status_code}")
                return self._safe_default()
            
            result = response.json()
            logger.info(f"Intent: {result.get('intent')}, RAG: {result.get('needs_rag')}, History: {result.get('needs_history')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._safe_default()
    
    def _safe_default(self) -> Dict:
        """Safe default when classification fails"""
        return {
            "intent": "academic",
            "needs_rag": True,
            "needs_history": True
        }
    
    async def close(self):
        await self.client.aclose()


# Global instance
intent_classifier = IntentClassifier()
```

#### 2.3 Update Context Service for Adaptive Context

```python
# python-backend/services/context_service.py

async def build_adaptive_context(
    self,
    user_id: str,
    course_id: str,
    user_message: str,
    access_token: str,
    intent: Dict,
    search_results: Optional[List[dict]] = None
) -> List[Dict]:
    """
    Build ChatML-formatted messages based on intent classification.
    
    Returns list of messages for ollama.chat():
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
        {"role": "user", "content": "current query"}
    ]
    """
    
    messages = []
    client = get_user_client(access_token)
    
    # 1. Build System Prompt
    system_parts = ["You are StudyMate, an AI tutor helping students learn effectively."]
    
    # Always include academic info (lightweight)
    academic = await self.get_academic_info(user_id, client)
    if academic:
        system_parts.append(f"\n[STUDENT PROFILE]")
        system_parts.append(f"Academic Level: {', '.join(academic.grade) if academic.grade else 'Not specified'}")
        system_parts.append(f"Semester: {academic.semester_type} semester, period {academic.semester}")
        system_parts.append(f"Subjects: {', '.join(academic.subject) if academic.subject else 'General'}")
    
    # Conditionally add preferences
    if intent.get("needs_rag") or intent["intent"] == "academic":
        prefs = await self.get_preferences(user_id, client)
        if prefs:
            system_parts.append(f"\n[LEARNING PREFERENCES]")
            system_parts.append(f"Detail Level: {prefs.detail_level:.1f}/1.0")
            system_parts.append(f"Learning Pace: {prefs.learning_pace}")
            system_parts.append(f"Prior Experience: {prefs.prior_experience}")
            system_parts.append(f"Prefers: {'Examples ' if prefs.example_preference > 0.6 else ''}{'Analogies ' if prefs.analogy_preference > 0.6 else ''}")
    
    # Conditionally add RAG chunks
    if intent.get("needs_rag") and search_results:
        system_parts.append(f"\n[COURSE MATERIALS]")
        for idx, result in enumerate(search_results[:3], 1):
            system_parts.append(f"\n{idx}. {result['name']} (relevance: {result['similarity_score']:.2f})")
            system_parts.append(f"   {result['excerpt'][:400]}...")
    
    system_parts.append("\n\nProvide clear, accurate answers tailored to the student's level and preferences.")
    
    messages.append({
        "role": "system",
        "content": "\n".join(system_parts)
    })
    
    # 2. Conditionally add chat history
    if intent.get("needs_history"):
        history = await self.get_chat_history(course_id, client, limit=6)
        for msg in history[-6:]:  # Last 3 exchanges
            messages.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            })
    
    # 3. Add current user query
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    logger.info(f"Built adaptive context: {len(messages)} messages, system prompt: {len(system_parts[0])} chars")
    
    return messages
```

#### 2.4 Update Chat Router

```python
# python-backend/routers/chat.py

from services.intent_classifier import intent_classifier

@router.post("/courses/{course_id}/chat", status_code=status.HTTP_201_CREATED)
async def save_chat_message(
    course_id: str,
    request: Request,
    chat_request: ChatRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Adaptive RAG chat with router-based intent classification.
    """
    try:
        client = get_user_client(user.access_token)
        
        # 1. Verify ownership
        # ... (existing code) ...
        
        # 2. Get user context for classification
        user_context = await context_service.get_user_context(
            user_id=user.id,
            course_id=course_id,
            access_token=user.access_token
        )
        
        # Extract subject and grade for router
        subject = user_context.academic.subject[0] if user_context.has_academic and user_context.academic.subject else "General"
        grade = user_context.academic.grade[0] if user_context.has_academic and user_context.academic.grade else "Bachelor"
        
        # 3. Classify Intent (Gemma 3 270M Router)
        logger.info("Step 1: Classifying query intent with router model...")
        intent = await intent_classifier.classify(
            query=chat_request.message,
            subject=subject,
            grade=grade
        )
        
        logger.info(f"Intent: {intent['intent']}, RAG: {intent['needs_rag']}, History: {intent['needs_history']}")
        
        # 4. Handle Safety Intent
        if intent["intent"] == "safety":
            logger.warning(f"Safety violation detected: {chat_request.message[:100]}")
            return ChatResponse(
                response="I can't help with that request. I'm designed to assist with educational content only.",
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
        
        # 5. Conditionally Search Materials
        search_results = []
        if intent["needs_rag"]:
            logger.info("Step 2: Performing RAG search...")
            search_results = await service_manager.processing_service.search_materials(
                course_id=course_id,
                query=chat_request.message,
                limit=3
            )
            logger.info(f"Found {len(search_results)} materials")
        else:
            logger.info("Step 2: Skipping RAG search (not needed)")
        
        # 6. Build Adaptive ChatML Messages
        logger.info("Step 3: Building adaptive context...")
        messages = await context_service.build_adaptive_context(
            user_id=user.id,
            course_id=course_id,
            user_message=chat_request.message,
            access_token=user.access_token,
            intent=intent,
            search_results=search_results
        )
        
        # 7. Generate Response with Core Model
        logger.info("Step 4: Generating response with core model...")
        response_text = await local_ai_service.generate_chat_response(
            messages=messages,
            attachments=chat_request.attachments
        )
        
        # 8. Save history
        # ... (existing code) ...
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Chat service error"})
```

#### 2.5 Update Local AI Service for ChatML

```python
# python-backend/services/local_ai_service.py

async def generate_chat_response(
    self,
    messages: List[Dict],
    attachments: Optional[List[FileAttachment]] = None
) -> str:
    """
    Generate response using ChatML format (ollama.chat API).
    
    Args:
        messages: List of {"role": "system/user/assistant", "content": "..."}
        attachments: Optional file attachments
    
    Returns:
        AI-generated response text
    """
    try:
        # For now, send messages as JSON to /router endpoint
        # Later, we'll add a /chat endpoint to brain.py
        
        payload = {
            "messages": messages,
            "model": "studymate"
        }
        
        response = await self.client.post(
            f"{self.brain_url}/chat",
            json=payload
        )
        
        if response.status_code != 200:
            raise LocalAIAPIError(f"Brain service error: {response.text}")
        
        response_data = response.json()
        return response_data.get("response", "")
        
    except Exception as e:
        logger.error(f"Chat generation error: {e}")
        raise LocalAIAPIError(str(e))
```

#### 2.6 Add Chat Endpoint to Brain Service

```python
# ai-brain/brain.py

@app.post("/chat")
async def chat_endpoint(request: dict):
    """
    ChatML-based chat endpoint using ollama.chat() API.
    Replaces the old /router endpoint for text-only queries.
    """
    try:
        messages = request.get("messages", [])
        model = request.get("model", CORE_MODEL)
        
        logger.info(f"Chat request: {len(messages)} messages")
        
        # Use ollama.chat() API
        response = await client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.45,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "num_ctx": 4096,
                "num_predict": 1024
            }
        )
        
        response_text = response['message']['content']
        
        logger.info(f"Chat response generated: {len(response_text)} chars")
        
        return {
            "response": response_text,
            "model": model
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

### **Phase 3: Testing & Validation**

#### 3.1 Test Router Classification
```python
# test_router_classification.py

import asyncio
from services.intent_classifier import intent_classifier

async def test_classification():
    test_cases = [
        ("Hello!", "General", "Bachelor", "chat", False, False),
        ("Explain photosynthesis", "Biology", "Bachelor", "academic", True, False),
        ("Why did you say that?", "Physics", "Masters", "followup", False, True),
        ("Fix this code error", "Computer Science", "Bachelor", "debug", False, True),
    ]
    
    for query, subject, grade, expected_intent, expected_rag, expected_history in test_cases:
        result = await intent_classifier.classify(query, subject, grade)
        
        print(f"\nQuery: {query}")
        print(f"Expected: intent={expected_intent}, rag={expected_rag}, history={expected_history}")
        print(f"Got: intent={result['intent']}, rag={result['needs_rag']}, history={result['needs_history']}")
        print(f"✓ PASS" if result['intent'] == expected_intent else "✗ FAIL")

asyncio.run(test_classification())
```

#### 3.2 Test End-to-End Flow
```bash
# Start services
cd ai-brain && python brain.py &
cd python-backend && uvicorn main:app --reload &

# Test with curl
curl -X POST http://localhost:8000/api/courses/test-course-id/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'

curl -X POST http://localhost:8000/api/courses/test-course-id/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain photosynthesis from my notes"}'
```

---

## 📊 Expected Performance Improvements

| Query Type | Current Tokens | With Router | Savings | Speed Improvement |
|------------|----------------|-------------|---------|-------------------|
| Chitchat | ~2000 | ~200 | 90% | 30-40% faster |
| Simple Q&A | ~2000 | ~800 | 60% | 20-30% faster |
| Material Query | ~2000 | ~1500 | 25% | 10-15% faster |
| Complex Study | ~2000 | ~2000 | 0% | Same |

---

## 🎯 Success Criteria

1. ✅ Router model achieves >90% classification accuracy
2. ✅ Chitchat queries skip RAG search (save 200-300ms)
3. ✅ Safety queries are blocked immediately
4. ✅ Follow-up questions use history correctly
5. ✅ Academic queries get full RAG context
6. ✅ No regression in response quality
7. ✅ Overall latency reduced by 15-30%

---

## 🚀 Deployment Checklist

- [ ] Fine-tune Gemma 3 270M router model
- [ ] Test router classification accuracy
- [ ] Add `/classify` endpoint to brain.py
- [ ] Create `intent_classifier.py` service
- [ ] Update `context_service.py` for adaptive context
- [ ] Update `chat.py` router to use classification
- [ ] Add `/chat` endpoint to brain.py for ChatML
- [ ] Update `local_ai_service.py` for ChatML format
- [ ] Test end-to-end flow
- [ ] Monitor performance metrics
- [ ] Deploy to production

---

## 📝 Notes

- Router model (Gemma 3 270M) stays loaded in VRAM (~270MB)
- Classification adds ~10-20ms latency (negligible)
- Fallback to safe defaults if classification fails
- ChatML format aligns with Qwen model training
- History is now properly managed in message format
- System prompt dynamically constructed based on needs

---

**Status**: Ready for implementation
**Next Step**: Fine-tune router model with `dataset_router/`
