# Supabase Spec Migration to Python Backend

## Overview

The Supabase database setup spec has been updated to use the existing Python FastAPI backend instead of creating a separate Node.js/TypeScript backend.

## What Changed

### Architecture
- **Before**: Spec assumed Node.js/Express backend with TypeScript
- **After**: Spec now uses existing Python FastAPI backend (`python-backend/`)

### Key Updates

#### 1. Design Document (`.kiro/specs/supabase-database-setup/design.md`)
- Updated technology stack to reflect Python 3.11+ with FastAPI
- Changed architecture diagram to show Python backend integration
- Replaced TypeScript examples with Python/FastAPI examples
- Updated Supabase client initialization for Python
- Added FastAPI route examples
- Updated Hypothesis testing strategies for Python

#### 2. Tasks Document (`.kiro/specs/supabase-database-setup/tasks.md`)
- Changed from `@supabase/supabase-js` (npm) to `supabase-py` (pip)
- Updated all file paths from `server/` to `python-backend/`
- Changed TypeScript files (`.ts`) to Python files (`.py`)
- Updated migration script location to `python-backend/migrations/`
- Changed from TypeScript types to Pydantic models
- Updated all router paths to use Python naming conventions
- Updated test framework from fast-check to Hypothesis (already installed)
- Changed test file locations to `python-backend/tests/`

#### 3. Environment Configuration
- Updated `python-backend/.env.example` to include Supabase configuration
- Root `.env.example` already had Supabase config (no changes needed)

### File Structure

```
python-backend/
├── main.py                          # FastAPI app (existing)
├── config.py                        # Config management (existing, needs Supabase vars)
├── requirements.txt                 # Dependencies (needs supabase-py)
├── .env.example                     # Updated with Supabase config
├── migrations/                      # NEW - SQL migration files
│   ├── 001_enable_extensions.sql
│   ├── 002_create_tables.sql
│   ├── 003_create_rls_policies.sql
│   └── 004_rollback.sql
├── scripts/                         # NEW - Migration scripts
│   └── run_migrations.py
├── services/
│   ├── local_ai_service.py         # Local AI Brain integration
│   ├── brain_manager.py            # Brain process manager
│   ├── supabase_client.py          # NEW - Supabase client
│   └── auth_service.py             # NEW - Auth utilities
├── routers/
│   ├── chat.py                     # Existing (needs Supabase integration)
│   ├── auth.py                     # NEW - Authentication endpoints
│   ├── academic.py                 # NEW - Academic profile endpoints
│   ├── preferences.py              # NEW - Preferences endpoints
│   ├── courses.py                  # NEW - Course management endpoints
│   └── materials.py                # NEW - Materials management endpoints
├── models/
│   ├── schemas.py                  # Existing Pydantic models
│   └── database.py                 # NEW - Database models
├── middleware/
│   ├── rate_limiter.py             # Existing
│   ├── logging_middleware.py       # Existing
│   └── auth_middleware.py          # NEW - JWT auth middleware
└── tests/                          # NEW - Test suite
    ├── conftest.py                 # Test configuration
    ├── strategies.py               # Hypothesis strategies
    ├── test_auth.py
    ├── test_academic.py
    ├── test_preferences.py
    ├── test_courses.py
    ├── test_materials.py
    ├── test_chat.py
    └── test_rls.py
```

## Requirements Document

The requirements document remains unchanged as it describes the system requirements independent of implementation technology.

## Next Steps

1. **Review the updated spec documents**:
   - `.kiro/specs/supabase-database-setup/design.md`
   - `.kiro/specs/supabase-database-setup/tasks.md`

2. **Start implementation** by executing tasks from the tasks.md file

3. **Key dependencies to add**:
   ```bash
   cd python-backend
   pip install supabase>=2.0.0
   ```

4. **Environment variables to configure** in `python-backend/.env`:
   ```
   SUPABASE_URL=https://[project-ref].supabase.co
   SUPABASE_ANON_KEY=[anon-key]
   SUPABASE_SERVICE_ROLE_KEY=[service-role-key]
   ```

## Benefits of Python Backend Approach

1. **Consistency**: All backend logic in one language (Python)
2. **Existing Infrastructure**: Leverages existing FastAPI setup, middleware, and configuration
3. **Unified Deployment**: Single Python backend service instead of multiple services
4. **Shared Dependencies**: Reuse existing dependencies like python-dotenv, FastAPI, etc.
5. **Simpler Architecture**: No need to coordinate between Node.js and Python backends

## Integration with Existing Chat Feature

The chat integration (`python-backend/routers/chat.py`) uses the Local AI Brain service:
- Store chat history in Supabase `chat_history` table
- Retrieve conversation context from Supabase
- Associate chats with courses and users
- AI powered by Local AI Brain Service (Qwen 2.5, DeepSeek OCR, Whisper Turbo)

This creates a complete system where:
- Users authenticate via Supabase Auth
- User data stored in Supabase PostgreSQL
- AI chat powered by Local AI Brain Service
- Chat history persisted in Supabase
