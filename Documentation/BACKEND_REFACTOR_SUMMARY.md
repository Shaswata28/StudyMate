# Backend Refactor Summary - Training JSON Format

## Overview
Refactored the backend to send prompts in the **exact JSON structure** the StudyMate model was trained on, instead of using Alpaca format.

## Changes Made

### 1. **context_service.py** - New JSON Formatter
- **Added**: `format_training_json()` method
- **Purpose**: Formats user context into the training JSON structure
- **Structure**:
  ```json
  {
    "instruction": "user's question",
    "input": {
      "academic_info": {
        "grade": ["Bachelor"],
        "semester_type": "double",
        "semester": 1,
        "subject": ["Computer Science"]
      },
      "learning_preferences": {
        "detail_level": 0.7,
        "example_preference": 0.7,
        "analogy_preference": 0.5,
        "technical_language": 0.6,
        "structure_preference": 0.8,
        "visual_preference": 0.5,
        "learning_pace": "moderate",
        "prior_experience": "intermediate"
      },
      "rag_chunks": [
        {
          "material_id": "uuid",
          "name": "filename.pdf",
          "excerpt": "relevant text...",
          "similarity_score": 0.95,
          "file_type": "application/pdf"
        }
      ],
      "chat_history": [
        {"role": "user", "content": "..."},
        {"role": "model", "content": "..."}
      ]
    }
  }
  ```

### 2. **chat.py** - Updated Chat Endpoints
- **Changed**: Both `/api/chat` and `/api/courses/{course_id}/chat` endpoints
- **Before**: Sent Alpaca-formatted strings
- **After**: Send training JSON structure
- **Key Changes**:
  - Call `context_service.format_training_json()` instead of `format_context_prompt()`
  - Pass `search_results` directly (not formatted as text)
  - Set `history=None` (now included in JSON structure)

### 3. **local_ai_service.py** - JSON Support
- **Changed**: `generate_response()` method signature
- **Before**: `message: str`
- **After**: `message: Union[str, dict]`
- **Behavior**:
  - If `dict`: Converts to JSON string and sends to brain
  - If `str`: Sends as-is (backward compatibility)
- **Added**: `import json` and `Union` type

### 4. **ai-brain/brain.py** - JSON Input Handling
- **Changed**: `/router` endpoint prompt processing
- **Behavior**:
  1. Try to parse prompt as JSON
  2. If valid training JSON → use directly
  3. If raw text → wrap in minimal training JSON
  4. If Alpaca format → use as-is (backward compatibility)
- **Updated Options**:
  - `temperature`: 0.45 (matches training)
  - `top_p`: 0.9 (matches training)
  - `repeat_penalty`: 1.15 (matches training)
  - `num_predict`: 2048 (increased from default)
  - `stop`: `["<|endoftext|>"]` (simplified for JSON)

## Benefits

1. **Matches Training Format**: Model receives data exactly as it was trained
2. **Better Context**: All user preferences, academic info, and RAG chunks properly structured
3. **Longer Responses**: `num_predict: 2048` allows for detailed answers
4. **Consistent Parameters**: Temperature, top_p, repeat_penalty match training
5. **Backward Compatible**: Still handles string prompts for legacy code

## Testing Recommendations

1. **Test with full context**: User with preferences + academic info + course materials
2. **Test with partial context**: User without preferences or academic info
3. **Test with RAG**: Course with uploaded materials
4. **Test without RAG**: General chat without course context
5. **Test chat history**: Multi-turn conversations
6. **Verify output length**: Responses should be longer and more detailed

## Next Steps

1. **Update Modelfile**: Increase `num_predict` from 512 to 2048
2. **Rebuild model**: `ollama create studymate -f Modelfile`
3. **Restart services**: Backend and AI brain
4. **Test thoroughly**: Verify responses match expected quality

## Rollback Plan

If issues occur, revert these files:
- `python-backend/services/context_service.py`
- `python-backend/routers/chat.py`
- `python-backend/services/local_ai_service.py`
- `ai-brain/brain.py`

The old `format_context_prompt()` method was removed, so you'd need to restore it from git history.
