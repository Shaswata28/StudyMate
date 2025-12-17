# Design Document

## Overview

This design implements context-aware AI chat by enhancing the existing chat endpoint to retrieve and incorporate user preferences, academic information, previous conversation history, and course materials into the AI prompt. The system uses sequential history retrieval (chronological order) without embeddings for Phase 1, keeping the implementation simple and efficient.

## Architecture

### High-Level Flow

```
User Message
    ↓
Chat Endpoint (POST /api/courses/{course_id}/chat)
    ↓
[Parallel Context Retrieval]
    ├─→ Get User Preferences (personalized table)
    ├─→ Get Academic Info (academic table)
    ├─→ Get Chat History (chat_history table, last 10)
    └─→ Search Materials (existing RAG, top 3)
    ↓
Context Formatter
    ↓
Enhanced AI Prompt
    ↓
Local AI Service
    ↓
AI Response
    ↓
Save to Database
    ↓
Return to User
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                     Chat Router                             │
│  (python-backend/routers/chat.py)                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  save_chat_message()                                 │  │
│  │  1. Verify course ownership                          │  │
│  │  2. Retrieve all context (parallel)                  │  │
│  │  3. Format enhanced prompt                           │  │
│  │  4. Call AI service                                  │  │
│  │  5. Save conversation                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Context Retrieval Service                      │
│  (python-backend/services/context_service.py) [NEW]        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  get_user_context()                                  │  │
│  │  ├─ get_preferences()                                │  │
│  │  ├─ get_academic_info()                              │  │
│  │  ├─ get_chat_history()                               │  │
│  │  └─ format_context_prompt()                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Supabase Database                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ personalized │  │   academic   │  │ chat_history │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Context Service (NEW)

**File:** `python-backend/services/context_service.py`

**Purpose:** Centralized service for retrieving and formatting user context

**Interface:**

```python
class ContextService:
    """Service for retrieving user context for AI chat."""
    
    async def get_user_context(
        self,
        user_id: str,
        course_id: str,
        access_token: str
    ) -> UserContext:
        """
        Retrieve all context for a user's chat request.
        
        Args:
            user_id: User's UUID
            course_id: Course UUID
            access_token: User's JWT token for Supabase
            
        Returns:
            UserContext object with preferences, academic info, and history
        """
        pass
    
    async def get_preferences(
        self,
        user_id: str,
        client: Client
    ) -> Optional[Dict]:
        """Retrieve user learning preferences."""
        pass
    
    async def get_academic_info(
        self,
        user_id: str,
        client: Client
    ) -> Optional[Dict]:
        """Retrieve user academic information."""
        pass
    
    async def get_chat_history(
        self,
        course_id: str,
        client: Client,
        limit: int = 10
    ) -> List[Message]:
        """Retrieve recent chat history for a course."""
        pass
    
    def format_context_prompt(
        self,
        context: UserContext,
        user_message: str,
        material_context: Optional[str] = None
    ) -> str:
        """Format all context into an enhanced AI prompt."""
        pass
```

### 2. Data Models (NEW)

**File:** `python-backend/models/schemas.py` (additions)

```python
from typing import Optional, List, Dict
from pydantic import BaseModel

class UserPreferences(BaseModel):
    """User learning preferences from personalized table."""
    detail_level: float
    example_preference: float
    analogy_preference: float
    technical_language: float
    structure_preference: float
    visual_preference: float
    learning_pace: str  # "slow", "moderate", "fast"
    prior_experience: str  # "beginner", "intermediate", "advanced", "expert"

class AcademicInfo(BaseModel):
    """User academic information from academic table."""
    grade: List[str]  # ["Bachelor", "Masters"]
    semester_type: str  # "double", "tri"
    semester: int
    subject: List[str]

class UserContext(BaseModel):
    """Complete user context for AI chat."""
    preferences: Optional[UserPreferences] = None
    academic: Optional[AcademicInfo] = None
    chat_history: List[Message] = []
    has_preferences: bool = False
    has_academic: bool = False
    has_history: bool = False
```

### 3. Enhanced Chat Router

**File:** `python-backend/routers/chat.py` (modifications)

**Changes:**
- Import and instantiate `ContextService`
- Modify `save_chat_message()` to retrieve user context
- Format enhanced prompt with all context
- Pass enhanced prompt to AI service

## Data Models

### Database Tables (Existing)

**personalized:**
```sql
CREATE TABLE personalized (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  prefs JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**academic:**
```sql
CREATE TABLE academic (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  grade TEXT[] NOT NULL,
  semester_type TEXT NOT NULL,
  semester INTEGER NOT NULL,
  subject TEXT[] NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**chat_history:**
```sql
CREATE TABLE chat_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  course_id UUID NOT NULL REFERENCES courses(id),
  history JSONB[] NOT NULL DEFAULT '{}',
  embedding VECTOR(384),  -- NULL for Phase 1
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Query Patterns

**Get User Preferences:**
```python
result = client.table("personalized")\
    .select("prefs")\
    .eq("id", user_id)\
    .single()\
    .execute()
```

**Get Academic Info:**
```python
result = client.table("academic")\
    .select("grade, semester_type, semester, subject")\
    .eq("id", user_id)\
    .single()\
    .execute()
```

**Get Chat History (Sequential):**
```python
result = client.table("chat_history")\
    .select("history")\
    .eq("course_id", course_id)\
    .order("created_at", desc=False)\  # Chronological
    .limit(10)\
    .execute()
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Context retrieval completeness
*For any* authenticated user with a complete profile, when retrieving user context, the system should return preferences, academic info, and chat history (if exists) without errors
**Validates: Requirements 1.1, 2.1, 3.1**

### Property 2: Graceful degradation
*For any* user with missing profile data, when retrieving user context, the system should return available context and use defaults for missing data without failing the request
**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 3: History ordering consistency
*For any* course with chat history, when retrieving messages, the returned messages should be ordered chronologically by created_at timestamp
**Validates: Requirements 1.2**

### Property 4: Context prompt structure
*For any* user context, when formatting the AI prompt, the prompt should include clearly separated sections for user profile, academic info, chat history, and materials (when present)
**Validates: Requirements 5.1, 5.2, 5.4**

### Property 5: History window limit
*For any* course with more than 10 chat messages, when retrieving history, the system should return exactly the 10 most recent messages
**Validates: Requirements 1.1, 6.2**

### Property 6: Parallel retrieval efficiency
*For any* context retrieval operation, when fetching preferences, academic info, and history, the total time should not exceed the sum of individual query times (indicating parallel execution)
**Validates: Requirements 6.1**

### Property 7: Default preferences consistency
*For any* user without preferences, when using default preferences, the defaults should match the moderate learning profile specification
**Validates: Requirements 2.3, 8.1**

### Property 8: Material context integration
*For any* chat request with course materials, when materials are found via RAG, the formatted prompt should include material excerpts before the user question
**Validates: Requirements 4.2, 4.4, 5.1**

## Error Handling

### Error Scenarios and Responses

| Scenario | Handling Strategy | User Impact |
|----------|------------------|-------------|
| **Preferences not found** | Use default moderate preferences, log warning | None - defaults used |
| **Academic info not found** | Proceed without academic context, log warning | Slightly less personalized |
| **Chat history query fails** | Proceed with empty history, log error | No conversation context |
| **Material search fails** | Proceed without materials, log error | No material grounding |
| **All context retrieval fails** | Proceed with just user message, log critical | Basic chat still works |
| **Context retrieval timeout** | Use partial context retrieved, log warning | Degraded personalization |
| **AI service unavailable** | Return 503 error to user | User sees error message |

### Default Values

**Default Preferences:**
```python
DEFAULT_PREFERENCES = {
    "detail_level": 0.5,
    "example_preference": 0.5,
    "analogy_preference": 0.5,
    "technical_language": 0.5,
    "structure_preference": 0.5,
    "visual_preference": 0.5,
    "learning_pace": "moderate",
    "prior_experience": "intermediate"
}
```

### Logging Strategy

```python
# Success logging
logger.info(f"Context retrieved for user {user_id}: "
           f"prefs={has_prefs}, academic={has_academic}, "
           f"history={len(history)} messages, materials={len(materials)}")

# Warning logging
logger.warning(f"Preferences not found for user {user_id}, using defaults")

# Error logging
logger.error(f"Failed to retrieve chat history for course {course_id}: {str(e)}")

# Performance logging
logger.info(f"Context retrieval completed in {elapsed_time:.2f}s")
```

## Testing Strategy

### Unit Tests

**Test Coverage:**
1. Context service methods (get_preferences, get_academic_info, get_chat_history)
2. Default preference application
3. Context prompt formatting
4. Error handling for missing data
5. History ordering and limiting

**Example Tests:**
```python
def test_get_preferences_success():
    """Test successful preference retrieval."""
    # Given: User with preferences
    # When: get_preferences() called
    # Then: Returns UserPreferences object

def test_get_preferences_not_found():
    """Test preference retrieval when user has no preferences."""
    # Given: User without preferences
    # When: get_preferences() called
    # Then: Returns None

def test_format_context_prompt_complete():
    """Test prompt formatting with all context."""
    # Given: Complete UserContext
    # When: format_context_prompt() called
    # Then: Prompt includes all sections

def test_format_context_prompt_partial():
    """Test prompt formatting with missing context."""
    # Given: Partial UserContext (no academic)
    # When: format_context_prompt() called
    # Then: Prompt omits academic section

def test_get_chat_history_ordering():
    """Test chat history is returned in chronological order."""
    # Given: Course with 5 messages
    # When: get_chat_history() called
    # Then: Messages ordered by created_at ASC

def test_get_chat_history_limit():
    """Test chat history respects limit."""
    # Given: Course with 20 messages
    # When: get_chat_history(limit=10) called
    # Then: Returns exactly 10 most recent messages
```

### Integration Tests

**Test Scenarios:**
1. End-to-end chat with complete user profile
2. End-to-end chat with missing preferences
3. End-to-end chat with missing academic info
4. End-to-end chat with no history
5. End-to-end chat with history > 10 messages
6. Performance test: context retrieval under 2 seconds

### Manual Testing

**Test Cases:**
1. Create user with complete profile → Send message → Verify AI response reflects preferences
2. Create user without preferences → Send message → Verify defaults used
3. Send 15 messages in a course → Verify only last 10 included in context
4. Compare AI responses with/without user profile → Verify personalization

## Implementation Notes

### Performance Considerations

1. **Parallel Queries:** Use `asyncio.gather()` to fetch preferences, academic info, and history simultaneously
2. **Query Limits:** Always limit chat history to 10 messages to prevent large data transfers
3. **Caching:** Consider caching user preferences/academic info for 5 minutes to reduce database load
4. **Timeout:** Set 2-second timeout for context retrieval, proceed with partial context if exceeded

### Prompt Engineering

**Context Prompt Template:**
```
--- USER LEARNING PROFILE ---
Detail Level: {detail_level} (0=brief, 1=detailed)
Example Preference: {example_preference} (0=few examples, 1=many examples)
Analogy Preference: {analogy_preference} (0=direct, 1=use analogies)
Technical Language: {technical_language} (0=simple, 1=technical)
Learning Pace: {learning_pace}
Prior Experience: {prior_experience}

Please adapt your response style to match these preferences.

--- ACADEMIC PROFILE ---
Education Level: {grade}
Current Semester: {semester} ({semester_type} semester system)
Subjects: {subjects}

Please tailor complexity and examples to this academic level.

--- PREVIOUS CONVERSATION ---
{chat_history}

--- RELEVANT COURSE MATERIALS ---
{materials}

--- CURRENT QUESTION ---
{user_message}
```

### Migration Path

**Phase 1 (Current):**
- Sequential history retrieval
- No embeddings generated
- Simple chronological ordering

**Phase 2 (Future):**
- Generate embeddings for chat history
- Semantic search on past conversations
- "Find similar discussions" feature
- Hybrid approach: recent + semantically similar

## Dependencies

- **Existing:** Supabase client, authentication service, local AI service
- **New:** Context service module
- **Database:** No schema changes needed (embedding column already exists, stays NULL)

## Security Considerations

1. **RLS Enforcement:** All queries use user's JWT token, ensuring data isolation
2. **Course Ownership:** Verify user owns course before retrieving history
3. **Data Minimization:** Only retrieve necessary fields from database
4. **Logging:** Avoid logging sensitive user data (preferences values, message content)

## Deployment Notes

1. No database migrations required
2. No new environment variables needed
3. Backward compatible - works with existing chat endpoint
4. Can be deployed incrementally (context service first, then integration)
