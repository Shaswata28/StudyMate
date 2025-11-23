# Design Document

## Overview

This design establishes a comprehensive Supabase database architecture for a personalized learning platform. The system leverages Supabase's managed PostgreSQL database with built-in authentication, Row Level Security (RLS), and real-time capabilities. The design prioritizes data security, scalability, and flexibility while supporting AI-powered personalized learning experiences through RAG (Retrieval-Augmented Generation) integration.

The implementation will be delivered in phases, starting with Supabase project initialization and authentication setup, followed by the complete database schema with all tables and relationships.

## Architecture

### Technology Stack

- **Database**: Supabase (PostgreSQL 15+)
- **Authentication**: Supabase Auth (built-in)
- **Backend**: Python 3.11+ with FastAPI (existing)
- **Supabase Client**: supabase-py (Python client library)
- **Environment Management**: python-dotenv for configuration (already configured)

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Supabase Cloud                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                      │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │   auth.users│  │  public.*    │  │   Storage   │  │  │
│  │  │  (managed)  │  │  (custom)    │  │   Buckets   │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Row Level Security (RLS) Policies             │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Supabase Auth Service                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API Keys & JWT
                            │
                ┌───────────▼──────────┐
                │   FastAPI Backend    │
                │  (python-backend/)   │
                │   - Supabase Client  │
                │   - Auth Routes      │
                │   - DB Routes        │
                └──────────────────────┘
```

### Database Schema Overview

The database consists of five main tables in the `public` schema, plus Supabase's managed `auth.users` table:

1. **auth.users** (Supabase managed) - Core authentication
2. **academic** - Academic information (grade, semester type, subjects)
3. **personalized** - JSONB-based personalization preferences
4. **courses** - User-created course containers
5. **materials** - Uploaded learning materials with Supabase Storage references
6. **chat_history** - Conversational AI logs with vector embeddings

## Components and Interfaces

### 1. Supabase Project Configuration

**Environment Variables** (`python-backend/.env` file):
```
# Existing Gemini configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=1024
GEMINI_TIMEOUT=30

# Rate limiting
RATE_LIMIT_REQUESTS=15
RATE_LIMIT_WINDOW=60

# CORS
ALLOWED_ORIGINS=http://localhost:8080

# Supabase configuration (NEW)
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=[anon-public-key]
SUPABASE_SERVICE_ROLE_KEY=[service-role-secret-key]
```

**Required Supabase Extensions**:
- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `vector` - pgvector extension for vector embeddings and similarity search
- `pg_trgm` - Text search capabilities (for future search features)

### 2. Authentication System

Supabase Auth handles all authentication operations:

**User Registration Flow**:
```
User submits email/password
    ↓
Supabase Auth creates auth.users record
    ↓
Email verification sent (optional but recommended)
    ↓
User confirms email
    ↓
Account activated
```

**Authentication Methods Supported**:
- Email/Password (primary)
- OAuth providers (future: Google, GitHub, etc.)
- Magic links (future)

**JWT Token Structure**:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "authenticated",
  "iat": 1234567890,
  "exp": 1234571490
}
```

### 3. Database Tables

#### Table: auth.users (Supabase Managed - Do Not Create)

This is Supabase's built-in authentication table that is automatically created and managed by Supabase Auth. We do not create this table manually.

**Built-in Fields** (managed by Supabase):
```sql
-- This table is automatically created by Supabase
-- DO NOT run CREATE TABLE for auth.users

-- Key fields available:
-- id UUID PRIMARY KEY (auto-generated UUID for user)
-- email TEXT UNIQUE NOT NULL (user's email for login)
-- encrypted_password TEXT NOT NULL (hashed password; never store plain-text)
-- confirmed_at TIMESTAMP (email confirmation timestamp)
-- last_sign_in_at TIMESTAMP (tracks login activity)
-- raw_user_meta_data JSONB (optional metadata during signup)
-- created_at TIMESTAMP
-- updated_at TIMESTAMP
```

**Important Notes**:
- This table is in the `auth` schema, not `public`
- Supabase automatically handles password hashing with bcrypt
- Email verification is managed through Supabase Auth settings
- Users cannot directly edit passwords (managed via Supabase Auth API)
- RLS is inherently managed by Supabase Auth
- Our custom tables reference `auth.users(id)` via foreign keys

**How We Use It**:
- Reference `auth.users(id)` in foreign key constraints
- Use `auth.uid()` function in RLS policies to get current authenticated user
- Access user data through Supabase Auth API, not direct SQL queries

---

#### Table: academic

Stores normalized academic information for each user with flexible grade and subject arrays.

```sql
CREATE TABLE academic (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    grade TEXT[] NOT NULL CHECK (grade <@ ARRAY['Bachelor', 'Masters']),
    semester_type TEXT NOT NULL CHECK (semester_type IN ('double', 'tri')),
    semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 12),
    subject TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger for auto-update timestamp
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER academic_update_trigger 
    BEFORE UPDATE ON academic 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();
```

**Field Explanations**:
- `id`: Primary key that directly references auth.users(id) for one-to-one relationship
- `grade`: Array allowing multiple degree levels (Bachelor, Masters)
- `semester_type`: Either 'double' (biannual) or 'tri' (trimester) system
- `semester`: Current semester number (1-12)
- `subject`: Array of subjects for flexible multi-subject support

**Indexes**:
- Primary key index on `id` (automatic)
- Consider GIN index on `grade` and `subject` arrays for efficient array queries

#### Table: personalized

Flexible JSONB storage for questionnaire responses and personalization data.

```sql
CREATE TABLE personalized (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    prefs JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reuse update_updated_at trigger
CREATE TRIGGER personalized_update_trigger 
    BEFORE UPDATE ON personalized 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();
```

**Example JSONB Structure**:
```json
{
  "detail_level": 0.6,
  "learning_pace": "moderate",
  "learning_style": "visual",
  "preferred_subjects": ["mathematics", "physics"],
  "ai_interaction_style": "detailed"
}
```

**Field Explanations**:
- `id`: Primary key that directly references auth.users(id) for one-to-one relationship
- `prefs`: JSONB field for flexible, schema-less preference storage enabling dynamic AI personalization

**Indexes**:
- Primary key index on `id` (automatic)
- GIN index on `prefs` for efficient JSONB queries

#### Table: courses

Organizational containers for learning materials and conversations.

```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER courses_update_trigger 
    BEFORE UPDATE ON courses 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();
```

**Field Explanations**:
- `id`: Unique identifier for the course
- `user_id`: Links course to owner (creator)
- `name`: Course name (e.g., "Biology 101")
- Timestamps track creation and modification

**Indexes**:
- `idx_courses_user_id` on `user_id` for efficient user course queries

#### Table: materials

Metadata for uploaded learning materials with Supabase Storage integration.

```sql
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    storage_object_id UUID REFERENCES storage.objects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER materials_update_trigger 
    BEFORE UPDATE ON materials 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();
```

**Field Explanations**:
- `id`: Unique identifier for the material record
- `course_id`: Links material to parent course
- `name`: User-friendly file name
- `storage_object_id`: References Supabase Storage bucket object for actual file content
- Processed chunks will be stored separately (future implementation)

**Indexes**:
- `idx_materials_course_id` on `course_id` for efficient course material queries
- `idx_materials_storage_object_id` on `storage_object_id` for storage lookups

#### Table: chat_history

Conversational logs stored as JSONB arrays with vector embeddings for RAG.

```sql
-- First enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    history JSONB[] NOT NULL DEFAULT '{}',
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER chat_history_update_trigger 
    BEFORE UPDATE ON chat_history 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

-- Index for vector similarity searches
CREATE INDEX chat_history_embedding_idx 
    ON chat_history 
    USING hnsw (embedding vector_cosine_ops);
```

**Field Explanations**:
- `id`: Unique identifier for the chat session/record
- `course_id`: Links conversation to parent course
- `history`: JSONB array storing message objects like `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
- `embedding`: Vector(384) for semantic search and RAG context retrieval (optional, for summarizing conversations)

**Message Format in JSONB Array**:
```json
[
  {"role": "user", "content": "What is photosynthesis?"},
  {"role": "assistant", "content": "Photosynthesis is..."}
]
```

**Indexes**:
- `idx_chat_history_course_id` on `course_id` for efficient course chat queries
- HNSW index on `embedding` for fast vector similarity searches

## Data Models

### Entity Relationship Diagram

```
┌─────────────────┐
│   auth.users    │
│   (Supabase)    │
└────────┬────────┘
         │
         │ 1:1
         ├──────────────────────────────────┐
         │                                  │
         │                                  │
┌────────▼────────────┐          ┌─────────▼──────────┐
│     academic        │          │   personalized     │
│                     │          │                    │
│ - grade[]           │          │ - prefs            │
│ - semester_type     │          │   (JSONB)          │
│ - semester          │          └────────────────────┘
│ - subject[]         │
└─────────────────────┘
         │
         │ 1:N
         │
┌────────▼────────────┐
│     courses         │
│                     │
│ - name              │
└────────┬────────────┘
         │
         │ 1:N
         ├──────────────────────────────────┐
         │                                  │
┌────────▼────────────┐          ┌─────────▼──────────┐
│    materials        │          │   chat_history     │
│                     │          │                    │
│ - name              │          │ - history[]        │
│ - storage_object_id │          │   (JSONB array)    │
│   → storage.objects │          │ - embedding        │
└─────────────────────┘          │   (VECTOR)         │
                                 └────────────────────┘
```

### Data Validation Rules

**Academic Table**:
- `grade`: Array must contain only 'Bachelor' or 'Masters' values
- `semester_type`: Must be either 'double' or 'tri'
- `semester`: Must be integer between 1 and 12
- `subject`: Array of text values, defaults to empty array
- One profile per user (enforced by PRIMARY KEY on id)

**Personalized Table**:
- `prefs`: Must be valid JSONB, defaults to empty object
- One preference record per user (enforced by PRIMARY KEY on id)

**Courses**:
- `name`: Required, text field
- User can create unlimited courses
- Must be owned by authenticated user

**Materials**:
- `name`: Required, text field for file name
- `storage_object_id`: Must reference valid storage.objects record
- Must belong to a course owned by the same user
- Cascade deletes when course or storage object is deleted

**Chat History**:
- `history`: JSONB array of message objects with 'role' and 'content' fields
- `embedding`: Optional VECTOR(384) for semantic search
- Must belong to a course owned by the user
- Chronologically ordered by `created_at`

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, several properties test similar database mechanisms and can be consolidated:

- **Foreign key integrity** is tested across multiple tables (3.5, 4.5, 5.2, 6.2, 7.3) - consolidated into Property 1
- **Query filtering by ownership** follows the same pattern across tables (3.3, 5.3, 6.4) - consolidated into Property 2
- **JSONB flexibility** (4.1, 4.2, 4.3) tests the same round-trip and update capability - consolidated into Property 3
- **Unique constraints** (3.2, 4.5) test the same constraint mechanism - consolidated into Property 4
- **RLS policies** (1.3, 8.4) both verify row-level security - consolidated into Property 5

### Correctness Properties

**Property 1: Referential integrity cascade behavior**

*For any* user with associated data (academic profile, preferences, courses, materials, chat history), when that user is deleted from auth.users, all dependent records in related tables should be automatically deleted via CASCADE constraints.

**Validates: Requirements 3.5, 4.5, 5.2, 6.2, 7.3**

---

**Property 2: Ownership-based query filtering**

*For any* user and any table with user_id foreign key (courses, materials, chat_history), querying records for that user should return only records where user_id matches the querying user, and should not return records belonging to other users.

**Validates: Requirements 3.3, 5.3, 6.4**

---

**Property 3: JSONB round-trip preservation**

*For any* valid JSON object stored in the user_preferences.preferences field, retrieving that record should return a JSONB object that is structurally equivalent to the original, and updating with a different JSON structure should succeed without schema modifications.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

---

**Property 4: Unique constraint enforcement**

*For any* user, attempting to create a second academic_profile or user_preferences record with the same user_id should fail with a unique constraint violation, ensuring one-to-one relationships.

**Validates: Requirements 3.2, 4.5**

---

**Property 5: Row Level Security policy coverage**

*For all* tables in the public schema (academic_profiles, user_preferences, courses, materials, chat_history), RLS must be enabled and policies must exist that restrict users to accessing only their own data based on user_id matching the authenticated user's JWT.

**Validates: Requirements 1.3, 8.4**

---

**Property 6: Authentication token generation**

*For any* valid user credentials (email and password), successful authentication should return a JWT token that contains the user's UUID in the 'sub' claim, has a valid expiration time, and can be used to authenticate subsequent requests.

**Validates: Requirements 2.2**

---

**Property 7: Invalid credential rejection**

*For any* authentication attempt with incorrect password or non-existent email, the authentication system should reject the request and return an error without revealing whether the email exists.

**Validates: Requirements 2.3**

---

**Property 8: Expired token rejection**

*For any* JWT token with an expiration timestamp in the past, attempts to use that token for authenticated requests should be rejected with an authentication error.

**Validates: Requirements 2.4**

---

**Property 9: Cascade deletion propagation**

*For any* course with associated materials and chat_history records, deleting that course should automatically delete all dependent materials and chat_history records via CASCADE constraints.

**Validates: Requirements 5.4**

---

**Property 10: Chat message chronological ordering**

*For any* course with multiple chat messages, retrieving chat history should return messages ordered by created_at timestamp in ascending order (oldest first).

**Validates: Requirements 7.4**

---

**Property 11: Material processing status transitions**

*For any* material record, the processing_status field should only contain valid enum values ('pending', 'processing', 'completed', 'failed'), and chunk_count should be updated when processing_status changes to 'completed'.

**Validates: Requirements 6.3**

---

**Property 12: Academic profile data persistence**

*For any* user with an academic profile, updating the grade_level and semester fields should persist the changes, and subsequent retrieval should return the updated values.

**Validates: Requirements 3.1, 3.4**

---

**Property 13: Course metadata completeness**

*For any* course creation, the stored record should include all required fields (id, user_id, name, created_at, updated_at) with non-null values, and optional fields (description, subject_area) should accept null values.

**Validates: Requirements 5.1, 5.5**

---

**Property 14: Material metadata completeness**

*For any* file upload, the materials record should capture all required metadata fields (filename, file_type, file_size_bytes, storage_path, uploaded_at) with non-null values.

**Validates: Requirements 6.1, 6.5**

---

**Property 15: Chat message role validation**

*For any* chat message, the role field should only accept the values 'user', 'assistant', or 'system', and attempting to insert a message with any other role value should fail with a constraint violation.

**Validates: Requirements 7.2**

## Error Handling

### Database Connection Errors

**Connection Failure**:
- Retry logic with exponential backoff (future backend implementation)
- Graceful degradation with user-friendly error messages
- Health check endpoint to monitor database connectivity

**Timeout Handling**:
- Query timeout set to 30 seconds for complex operations
- Connection pool timeout configuration
- Proper cleanup of stale connections

### Authentication Errors

**Invalid Credentials**:
- Return generic "Invalid email or password" message
- Do not reveal whether email exists (security best practice)
- Rate limiting on failed login attempts (Supabase built-in)

**Token Expiration**:
- Return 401 Unauthorized with clear error message
- Client should redirect to login page
- Refresh token flow for seamless re-authentication (future)

**Email Verification**:
- Block unverified users from accessing protected resources
- Provide resend verification email functionality
- Clear messaging about verification requirement

### Data Validation Errors

**Constraint Violations**:
- Unique constraint: "A record already exists for this user"
- Foreign key violation: "Referenced record does not exist"
- Check constraint: "Invalid value for field X"
- Not null violation: "Required field X is missing"

**JSONB Validation**:
- Malformed JSON: Return 400 Bad Request with parsing error
- Schema validation for expected preference fields (future)
- Size limits on JSONB fields to prevent abuse

**File Upload Errors**:
- File size exceeds limit: Return 413 Payload Too Large
- Unsupported file type: Return 400 Bad Request
- Storage quota exceeded: Return 507 Insufficient Storage

### RLS Policy Violations

**Unauthorized Access**:
- RLS policies return empty result sets (not errors)
- Attempting to access another user's data returns no rows
- Attempting to modify another user's data silently fails
- Audit logging for security monitoring (future)

## Testing Strategy

### Database Schema Testing

**Migration Testing**:
- Verify all tables are created with correct structure
- Verify all indexes are created
- Verify all foreign key constraints are established
- Verify all RLS policies are applied
- Test rollback migrations successfully revert changes

**Constraint Testing**:
- Test unique constraints prevent duplicates
- Test foreign key constraints prevent orphaned records
- Test check constraints enforce valid values
- Test not-null constraints prevent missing data
- Test cascade deletes propagate correctly

### Property-Based Testing

We will use **Hypothesis** (Python property-based testing library) to implement the correctness properties defined above.

**Configuration**:
- Minimum 100 iterations per property test
- Use Hypothesis strategies to generate valid test data
- Each property test must reference its design document property number

**Test Tagging Format**:
```python
# Feature: supabase-database-setup, Property 1: Referential integrity cascade behavior
@given(user_data=user_strategy())
def test_cascade_deletion(user_data):
    # Test implementation
    pass
```

**Property Test Coverage**:
- Property 1: Test cascade deletion with generated user data
- Property 2: Test query filtering with multiple users
- Property 3: Test JSONB round-trip with various JSON structures
- Property 4: Test unique constraints with duplicate attempts
- Property 5: Test RLS policies with different user contexts
- Property 6-8: Test authentication flows with generated credentials
- Property 9: Test course cascade with generated course data
- Property 10: Test message ordering with random timestamps
- Property 11: Test status transitions with generated materials
- Property 12-15: Test data persistence with generated records

**Hypothesis Strategies** (`python-backend/tests/strategies.py`):
```python
from hypothesis import strategies as st

# User data strategy
user_strategy = st.builds(
    dict,
    email=st.emails(),
    password=st.text(min_size=8, max_size=100)
)

# Academic profile strategy
academic_strategy = st.builds(
    dict,
    grade=st.lists(st.sampled_from(['Bachelor', 'Masters']), min_size=1, max_size=2),
    semester_type=st.sampled_from(['double', 'tri']),
    semester=st.integers(min_value=1, max_value=12),
    subject=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10)
)

# JSONB preferences strategy
preferences_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.text())
    ),
    min_size=1,
    max_size=20
)

# Course strategy
course_strategy = st.builds(
    dict,
    name=st.text(min_size=1, max_size=255)
)

# Material strategy
material_strategy = st.builds(
    dict,
    name=st.text(min_size=1, max_size=255)
)

# Chat message strategy
chat_message_strategy = st.builds(
    dict,
    role=st.sampled_from(['user', 'model']),
    content=st.text(min_size=1, max_size=2000)
)
```

### Unit Testing

Unit tests will complement property tests by covering specific examples and edge cases:

**Authentication Tests**:
- Test successful registration with valid email/password
- Test registration with duplicate email fails
- Test login with correct credentials succeeds
- Test login with wrong password fails
- Test email verification flow
- Test token expiration handling

**CRUD Operation Tests**:
- Test creating academic profile
- Test updating academic profile
- Test deleting user cascades to academic profile
- Test creating user preferences with JSONB
- Test updating JSONB preferences
- Test creating course
- Test querying user's courses
- Test uploading material metadata
- Test creating chat message

**Edge Cases**:
- Empty string handling in text fields
- Maximum length validation
- Null value handling in optional fields
- Concurrent updates to same record
- Large JSONB objects (size limits)
- Special characters in text fields
- Unicode handling in all text fields

**RLS Policy Tests**:
- Test user can read their own data
- Test user cannot read other user's data
- Test user can update their own data
- Test user cannot update other user's data
- Test user can delete their own data
- Test user cannot delete other user's data
- Test service role can bypass RLS

### Integration Testing

**End-to-End Flows**:
- Complete user registration → profile creation → course creation → material upload → chat interaction flow
- User authentication → token usage → data access flow
- Course creation → material upload → processing status update flow
- Multi-user isolation testing (ensure users cannot access each other's data)

**Database Performance Tests**:
- Query performance with large datasets
- Index effectiveness verification
- Connection pool behavior under load
- Concurrent transaction handling

## Implementation Notes

### Supabase Project Setup Steps

1. **Create Project**:
   - Go to https://supabase.com/dashboard
   - Click "New Project"
   - Choose project name and strong database password
   - Select region closest to target users
   - Wait for project provisioning (~2 minutes)

2. **Enable Extensions**:
   ```sql
   -- Run in Supabase SQL Editor
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   CREATE EXTENSION IF NOT EXISTS "vector";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";
   ```

3. **Configure Authentication**:
   - Navigate to Authentication → Settings
   - Enable email confirmation (recommended)
   - Set site URL for email redirects
   - Configure email templates (optional)
   - Set JWT expiry time (default: 1 hour)

4. **Set Up Environment Variables**:
   - Copy project URL and API keys from Settings → API
   - Store in `.env` file (never commit to version control)
   - Add `.env` to `.gitignore`

### Migration Strategy

**Initial Migration** (`001_initial_schema.sql`):
- Create all tables with constraints
- Create all indexes
- Enable RLS on all tables
- Create initial RLS policies

**RLS Policies for All Tables**:

```sql
-- Academic Table RLS
ALTER TABLE academic ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users edit own academic data" 
ON academic FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);

-- Personalized Table RLS
ALTER TABLE personalized ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users edit own prefs" 
ON personalized FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);

-- Courses Table RLS
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own courses" 
ON courses FOR ALL 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- Materials Table RLS (via course ownership)
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own materials" 
ON materials FOR ALL 
USING (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
) 
WITH CHECK (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
);

-- Chat History Table RLS (via course ownership)
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own chat history" 
ON chat_history FOR ALL 
USING (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
) 
WITH CHECK (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
);
```

**RLS Policy Explanation**:
- **academic** and **personalized**: Direct user ownership via `id = auth.uid()`
- **courses**: Direct user ownership via `user_id = auth.uid()`
- **materials** and **chat_history**: Indirect ownership through course relationship (users can only access materials/chats for courses they own)

### Python FastAPI Integration

**Supabase Client Setup** (`python-backend/services/supabase_client.py`):
```python
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin operations
)

# For client-side operations (with RLS)
def get_user_client(access_token: str) -> Client:
    """Create a Supabase client with user's JWT token for RLS enforcement."""
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY"),
        options={"headers": {"Authorization": f"Bearer {access_token}"}}
    )
```

**Example Operations**:
```python
# User registration
auth_response = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure_password"
})

# User login
auth_response = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "secure_password"
})

# Create academic profile
profile = supabase.table("academic").insert({
    "id": auth_response.user.id,
    "grade": ["Bachelor"],
    "semester_type": "double",
    "semester": 3,
    "subject": ["Computer Science", "Mathematics"]
}).execute()

# Create personalized preferences
prefs = supabase.table("personalized").insert({
    "id": auth_response.user.id,
    "prefs": {
        "detail_level": 0.7,
        "learning_pace": "moderate",
        "learning_style": "visual"
    }
}).execute()

# Query user's courses (with RLS)
user_client = get_user_client(auth_response.session.access_token)
courses = user_client.table("courses").select("*").execute()
```

**FastAPI Route Example** (`python-backend/routers/courses.py`):
```python
from fastapi import APIRouter, Depends, HTTPException
from services.supabase_client import get_user_client
from models.schemas import CourseCreate, CourseResponse

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("/", response_model=list[CourseResponse])
async def get_courses(user_token: str = Depends(get_current_user_token)):
    """Get all courses for the authenticated user."""
    client = get_user_client(user_token)
    response = client.table("courses").select("*").execute()
    return response.data

@router.post("/", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    user_token: str = Depends(get_current_user_token)
):
    """Create a new course for the authenticated user."""
    client = get_user_client(user_token)
    user = client.auth.get_user(user_token)
    
    response = client.table("courses").insert({
        "user_id": user.user.id,
        "name": course.name
    }).execute()
    
    return response.data[0]
```

### Security Considerations

**Environment Variables**:
- Never commit `.env` files
- Use different keys for development/production
- Rotate service role key periodically
- Limit service role key usage to backend only

**RLS Policies**:
- Always enable RLS on tables with user data
- Test policies thoroughly with different user contexts
- Use `auth.uid()` function to get authenticated user ID
- Service role bypasses RLS (use carefully)

**Password Security**:
- Supabase handles password hashing (bcrypt)
- Enforce minimum password length (8+ characters)
- Consider password strength requirements
- Implement rate limiting on auth endpoints

**Data Validation**:
- Validate all inputs on backend before database operations
- Use parameterized queries (Supabase client handles this)
- Sanitize user-provided text for XSS prevention
- Validate file uploads before storage

### Monitoring and Maintenance

**Database Monitoring**:
- Monitor query performance in Supabase dashboard
- Set up alerts for high error rates
- Track storage usage and plan upgrades
- Monitor connection pool utilization

**Backup Strategy**:
- Supabase provides automatic daily backups
- Test backup restoration process
- Consider point-in-time recovery for production
- Export critical data periodically

**Schema Evolution**:
- Use numbered migration files
- Test migrations on staging environment first
- Always provide rollback migrations
- Document breaking changes clearly
- Version API alongside schema changes
