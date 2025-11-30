# Database Schema Documentation

## Overview

This document provides comprehensive documentation for the Supabase database schema used in the personalized learning platform. The database is built on PostgreSQL 15+ and leverages Supabase's managed authentication, Row Level Security (RLS), and real-time capabilities.

**Database Provider**: Supabase (PostgreSQL 15+)  
**Schema Version**: 1.0  
**Last Updated**: 2024

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Database Extensions](#database-extensions)
4. [Table Definitions](#table-definitions)
5. [Indexes](#indexes)
6. [Row Level Security (RLS) Policies](#row-level-security-rls-policies)
7. [Triggers and Functions](#triggers-and-functions)
8. [Data Validation Rules](#data-validation-rules)
9. [Common Query Examples](#common-query-examples)
10. [Migration Scripts](#migration-scripts)

---

## Architecture Overview

The database consists of **6 main tables** organized around user authentication and personalized learning:

### Core Tables

1. **auth.users** (Supabase managed) - User authentication and identity
2. **academic** - Academic profile information (grade, semester, subjects)
3. **personalized** - JSONB-based learning preferences
4. **courses** - User-created organizational containers
5. **materials** - Uploaded learning materials metadata
6. **chat_history** - AI conversation logs with vector embeddings

### Key Design Principles

- **Data Isolation**: Row Level Security (RLS) ensures users can only access their own data
- **Referential Integrity**: Foreign key constraints with CASCADE deletion maintain data consistency
- **Flexibility**: JSONB fields allow schema-less preference storage
- **Scalability**: Proper indexing on frequently queried columns
- **AI Integration**: Vector embeddings support RAG (Retrieval-Augmented Generation)

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        auth.users                               │
│                    (Supabase Managed)                           │
│                                                                 │
│  - id (UUID, PK)                                                │
│  - email (TEXT, UNIQUE)                                         │
│  - encrypted_password (TEXT)                                    │
│  - confirmed_at (TIMESTAMP)                                     │
│  - created_at (TIMESTAMP)                                       │
│  - updated_at (TIMESTAMP)                                       │
└────────────┬────────────────────────────────────┬──────────────┘
             │                                    │
             │ 1:1                                │ 1:1
             │                                    │
┌────────────▼──────────────┐        ┌───────────▼──────────────┐
│        academic           │        │      personalized        │
│                           │        │                          │
│ - id (UUID, PK, FK)       │        │ - id (UUID, PK, FK)      │
│ - grade (TEXT[])          │        │ - prefs (JSONB)          │
│ - semester_type (TEXT)    │        │ - created_at (TIMESTAMPTZ)│
│ - semester (INTEGER)      │        │ - updated_at (TIMESTAMPTZ)│
│ - subject (TEXT[])        │        └──────────────────────────┘
│ - created_at (TIMESTAMPTZ)│
│ - updated_at (TIMESTAMPTZ)│
└───────────────────────────┘
             │
             │ 1:N
             │
┌────────────▼──────────────┐
│         courses           │
│                           │
│ - id (UUID, PK)           │
│ - user_id (UUID, FK)      │
│ - name (TEXT)             │
│ - created_at (TIMESTAMPTZ)│
│ - updated_at (TIMESTAMPTZ)│
└────────────┬──────────────┘
             │
             │ 1:N
             ├─────────────────────────────────┐
             │                                 │
┌────────────▼──────────────┐    ┌────────────▼──────────────┐
│       materials           │    │      chat_history         │
│                           │    │                           │
│ - id (UUID, PK)           │    │ - id (UUID, PK)           │
│ - course_id (UUID, FK)    │    │ - course_id (UUID, FK)    │
│ - name (TEXT)             │    │ - history (JSONB[])       │
│ - file_path (TEXT)        │    │ - embedding (VECTOR(384)) │
│ - file_type (TEXT)        │    │ - created_at (TIMESTAMPTZ)│
│ - file_size (BIGINT)      │    │ - updated_at (TIMESTAMPTZ)│
│ - created_at (TIMESTAMPTZ)│    └───────────────────────────┘
│ - updated_at (TIMESTAMPTZ)│
└───────────────────────────┘

Legend:
  PK = Primary Key
  FK = Foreign Key
  1:1 = One-to-One Relationship
  1:N = One-to-Many Relationship
```

---

## Database Extensions

The following PostgreSQL extensions are enabled to support advanced functionality:


| Extension | Purpose | Usage |
|-----------|---------|-------|
| **uuid-ossp** | UUID generation | Provides `uuid_generate_v4()` for automatic UUID generation in primary keys |
| **pgcrypto** | Cryptographic functions | Provides encryption and hashing functions for secure data handling |
| **vector** | Vector embeddings | Provides `VECTOR` data type for storing embeddings and similarity search operations (RAG) |
| **pg_trgm** | Text search | Provides trigram-based similarity and pattern matching for future search features |

**Migration File**: `python-backend/migrations/001_enable_extensions.sql`

---

## Table Definitions

### 1. auth.users (Supabase Managed)

**⚠️ Important**: This table is automatically created and managed by Supabase Auth. Do not create or modify this table manually.

**Purpose**: Core authentication and user identity management.

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier (auto-generated) |
| `email` | TEXT | UNIQUE, NOT NULL | User's email address for login |
| `encrypted_password` | TEXT | NOT NULL | Bcrypt-hashed password (never plain text) |
| `confirmed_at` | TIMESTAMP | | Email confirmation timestamp |
| `last_sign_in_at` | TIMESTAMP | | Last login timestamp |
| `raw_user_meta_data` | JSONB | | Optional metadata during signup |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Key Features**:
- Automatic password hashing with bcrypt
- Email verification workflow
- JWT token generation
- Managed by Supabase Auth API

**Access Pattern**:
- Reference via foreign keys: `REFERENCES auth.users(id)`
- Use `auth.uid()` function in RLS policies to get current authenticated user

---

### 2. academic

**Purpose**: Stores normalized academic information for each user (grade level, semester, subjects).

**Relationship**: One-to-one with `auth.users`

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, FK → auth.users(id) ON DELETE CASCADE | User ID (same as auth.users.id) |
| `grade` | TEXT[] | NOT NULL, CHECK (grade <@ ARRAY['Bachelor', 'Masters']) | Array of degree levels |
| `semester_type` | TEXT | NOT NULL, CHECK (semester_type IN ('double', 'tri')) | Semester system type |
| `semester` | INTEGER | NOT NULL, CHECK (semester BETWEEN 1 AND 12) | Current semester number |
| `subject` | TEXT[] | NOT NULL, DEFAULT '{}' | Array of subjects (see valid subjects below) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp (auto-updated) |

**Valid Subjects**:
- `computer science`
- `electrical and electronics engineering`
- `english`
- `business administration`
- `economics`

**Constraints**:
- At least one grade must be specified: `CHECK (array_length(grade, 1) > 0)`
- Subjects must be from the valid list

**Indexes**:
- `idx_academic_grade` - GIN index on `grade` array for efficient array queries
- `idx_academic_subject` - GIN index on `subject` array for efficient array queries

**Migration File**: `python-backend/migrations/002_create_tables.sql`

---

### 3. personalized

**Purpose**: Stores flexible JSONB-based personalization preferences from user questionnaires.

**Relationship**: One-to-one with `auth.users`

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, FK → auth.users(id) ON DELETE CASCADE | User ID (same as auth.users.id) |
| `prefs` | JSONB | NOT NULL, DEFAULT '{}' | Flexible preference object |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp (auto-updated) |

**JSONB Structure** (prefs field):

```json
{
  "detail_level": 0.7,              // Float 0-1: preference for detailed explanations
  "example_preference": 0.8,        // Float 0-1: preference for examples
  "analogy_preference": 0.6,        // Float 0-1: preference for analogies
  "technical_language": 0.5,        // Float 0-1: preference for technical terms
  "structure_preference": 0.7,      // Float 0-1: preference for structured content
  "visual_preference": 0.9,         // Float 0-1: preference for visual aids
  "learning_pace": "moderate",      // String: "slow", "moderate", or "fast"
  "prior_experience": "intermediate" // String: "beginner", "intermediate", "advanced", "expert"
}
```

**Indexes**:
- `idx_personalized_prefs` - GIN index on `prefs` for efficient JSONB queries

**Migration File**: `python-backend/migrations/002_create_tables.sql`

---

### 4. courses

**Purpose**: Organizational containers for grouping learning materials and conversations by topic/subject.

**Relationship**: One-to-many with `auth.users` (user can have multiple courses)

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique course identifier |
| `user_id` | UUID | NOT NULL, FK → auth.users(id) ON DELETE CASCADE | Course owner |
| `name` | TEXT | NOT NULL | Course name (e.g., "Biology 101") |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Course creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp (auto-updated) |

**Indexes**:
- `idx_courses_user_id` - B-tree index on `user_id` for efficient user course queries

**Migration File**: `python-backend/migrations/002_create_tables.sql`

---

### 5. materials

**Purpose**: Metadata for uploaded learning materials (PDFs, documents, images) with Supabase Storage integration.

**Relationship**: One-to-many with `courses` (course can have multiple materials)

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique material identifier |
| `course_id` | UUID | NOT NULL, FK → courses(id) ON DELETE CASCADE | Parent course |
| `name` | TEXT | NOT NULL | User-friendly file name |
| `file_path` | TEXT | NOT NULL | Storage path: `{user_id}/{course_id}/{filename}` |
| `file_type` | TEXT | NOT NULL | MIME type (e.g., `application/pdf`, `image/jpeg`) |
| `file_size` | BIGINT | NOT NULL | File size in bytes (max 50MB = 52,428,800 bytes) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Upload timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp (auto-updated) |

**Storage Path Format**: `{user_id}/{course_id}/{filename}`

**Supported File Types**:
- PDFs: `application/pdf`
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`

**Indexes**:
- `idx_materials_course_id` - B-tree index on `course_id` for efficient course material queries
- `idx_materials_file_path` - B-tree index on `file_path` for storage lookups

**Migration File**: `python-backend/migrations/002_create_tables.sql`

---

### 6. chat_history

**Purpose**: Conversational AI logs stored as JSONB arrays with vector embeddings for RAG (Retrieval-Augmented Generation).

**Relationship**: One-to-many with `courses` (course can have multiple chat records)

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique chat record identifier |
| `course_id` | UUID | NOT NULL, FK → courses(id) ON DELETE CASCADE | Parent course |
| `history` | JSONB[] | NOT NULL, DEFAULT '{}' | Array of message objects |
| `embedding` | VECTOR(384) | | Vector embedding for semantic search (optional) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Chat creation timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp (auto-updated) |

**JSONB Array Structure** (history field):

```json
[
  {
    "role": "user",
    "content": "What is photosynthesis?"
  },
  {
    "role": "model",
    "content": "Photosynthesis is the process by which plants..."
  }
]
```

**Message Roles**:
- `user` - User-generated messages
- `model` - AI-generated responses

**Vector Embeddings**:
- Dimension: 384 (compatible with sentence-transformers models)
- Used for semantic similarity search and context retrieval
- Indexed with HNSW (Hierarchical Navigable Small World) for fast approximate nearest neighbor search

**Indexes**:
- `idx_chat_history_course_id` - B-tree index on `course_id` for efficient course chat queries
- `chat_history_embedding_idx` - HNSW index on `embedding` using cosine distance for vector similarity search

**Migration File**: `python-backend/migrations/002_create_tables.sql`

---

## Indexes

Indexes are created to optimize query performance on frequently accessed columns.

### Primary Key Indexes (Automatic)

All tables have automatic indexes on their primary keys:
- `academic.id`
- `personalized.id`
- `courses.id`
- `materials.id`
- `chat_history.id`

### Custom Indexes

| Index Name | Table | Column(s) | Type | Purpose |
|------------|-------|-----------|------|---------|
| `idx_academic_grade` | academic | grade | GIN | Efficient array containment queries on grade levels |
| `idx_academic_subject` | academic | subject | GIN | Efficient array containment queries on subjects |
| `idx_personalized_prefs` | personalized | prefs | GIN | Efficient JSONB queries on preference fields |
| `idx_courses_user_id` | courses | user_id | B-tree | Fast lookup of user's courses |
| `idx_materials_course_id` | materials | course_id | B-tree | Fast lookup of course materials |
| `idx_materials_file_path` | materials | file_path | B-tree | Fast storage path lookups |
| `idx_chat_history_course_id` | chat_history | course_id | B-tree | Fast lookup of course chat history |
| `chat_history_embedding_idx` | chat_history | embedding | HNSW | Fast vector similarity search for RAG |

### Index Usage Examples

**GIN Indexes** (Generalized Inverted Index):
- Used for array and JSONB columns
- Supports containment operators (`@>`, `<@`)
- Example: `WHERE grade @> ARRAY['Bachelor']`

**B-tree Indexes**:
- Default index type for scalar values
- Supports equality and range queries
- Example: `WHERE user_id = 'uuid-value'`

**HNSW Indexes** (Hierarchical Navigable Small World):
- Used for vector similarity search
- Supports approximate nearest neighbor queries
- Example: `ORDER BY embedding <=> query_vector LIMIT 10`

---

## Row Level Security (RLS) Policies

Row Level Security ensures data isolation by restricting access based on the authenticated user's JWT token.

### Security Model

- **Enabled on all tables**: RLS is enabled on `academic`, `personalized`, `courses`, `materials`, and `chat_history`
- **User identification**: Uses `auth.uid()` function to get the authenticated user's UUID from JWT token
- **Policy enforcement**: Policies apply to SELECT, INSERT, UPDATE, and DELETE operations
- **Service role bypass**: Service role key bypasses RLS (use carefully in backend only)

### Policy Definitions

#### 1. academic Table

**Policy Name**: `Users edit own academic data`

```sql
CREATE POLICY "Users edit own academic data" 
ON academic 
FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);
```

**Effect**: Users can only read, insert, update, and delete their own academic profile (where `id` matches their user ID).

---

#### 2. personalized Table

**Policy Name**: `Users edit own prefs`

```sql
CREATE POLICY "Users edit own prefs" 
ON personalized 
FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);
```

**Effect**: Users can only read, insert, update, and delete their own preferences (where `id` matches their user ID).

---

#### 3. courses Table

**Policy Name**: `Users own courses`

```sql
CREATE POLICY "Users own courses" 
ON courses 
FOR ALL 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);
```

**Effect**: Users can only read, insert, update, and delete courses they own (where `user_id` matches their user ID).

---

#### 4. materials Table

**Policy Name**: `Users own materials`

```sql
CREATE POLICY "Users own materials" 
ON materials 
FOR ALL 
USING (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
) 
WITH CHECK (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
);
```

**Effect**: Users can only access materials for courses they own (indirect ownership through course relationship).

---

#### 5. chat_history Table

**Policy Name**: `Users own chat history`

```sql
CREATE POLICY "Users own chat history" 
ON chat_history 
FOR ALL 
USING (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
) 
WITH CHECK (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
);
```

**Effect**: Users can only access chat history for courses they own (indirect ownership through course relationship).

---

### RLS Testing

To test RLS policies, use different user contexts:

```sql
-- Set user context (simulates authenticated user)
SET request.jwt.claim.sub = 'user-uuid-here';

-- Query should only return data for this user
SELECT * FROM courses;

-- Reset to service role (bypasses RLS)
RESET request.jwt.claim.sub;
```

**Migration File**: `python-backend/migrations/003_create_rls_policies.sql`

---

## Triggers and Functions

### Automatic Timestamp Update Function

**Function Name**: `update_updated_at()`

**Purpose**: Automatically updates the `updated_at` column whenever a row is modified.

**Definition**:

```sql
CREATE OR REPLACE FUNCTION update_updated_at() 
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE plpgsql;
```

**Usage**: This function is attached to all tables via BEFORE UPDATE triggers.

### Triggers

All tables have triggers that automatically update the `updated_at` timestamp on modifications:

| Trigger Name | Table | Event | Function |
|--------------|-------|-------|----------|
| `academic_update_trigger` | academic | BEFORE UPDATE | update_updated_at() |
| `personalized_update_trigger` | personalized | BEFORE UPDATE | update_updated_at() |
| `courses_update_trigger` | courses | BEFORE UPDATE | update_updated_at() |
| `materials_update_trigger` | materials | BEFORE UPDATE | update_updated_at() |
| `chat_history_update_trigger` | chat_history | BEFORE UPDATE | update_updated_at() |

**Example**:

```sql
CREATE TRIGGER academic_update_trigger 
    BEFORE UPDATE ON academic 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();
```

**Migration File**: `python-backend/migrations/002_create_tables.sql`

---

## Data Validation Rules

### academic Table

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| `grade` | Must be subset of `['Bachelor', 'Masters']` | Invalid grade value |
| `grade` | Array must not be empty | At least one grade must be specified |
| `semester_type` | Must be `'double'` or `'tri'` | Invalid semester type |
| `semester` | Must be between 1 and 12 | Semester must be between 1 and 12 |
| `subject` | Must be subset of valid subjects list | Invalid subject |

### personalized Table

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| `prefs` | Must be valid JSONB | Invalid JSON format |
| `prefs.detail_level` | Float between 0 and 1 | Detail level must be 0-1 |
| `prefs.learning_pace` | Must be `'slow'`, `'moderate'`, or `'fast'` | Invalid learning pace |
| `prefs.prior_experience` | Must be `'beginner'`, `'intermediate'`, `'advanced'`, or `'expert'` | Invalid experience level |

### courses Table

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| `name` | Must not be empty | Course name is required |
| `name` | Max length 255 characters | Course name too long |

### materials Table

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| `name` | Must not be empty | File name is required |
| `file_size` | Must be positive | File size must be greater than 0 |
| `file_size` | Max 52,428,800 bytes (50MB) | File size exceeds 50MB limit |
| `file_type` | Must be valid MIME type | Invalid file type |

### chat_history Table

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| `history` | Must be valid JSONB array | Invalid history format |
| `history[].role` | Must be `'user'` or `'model'` | Invalid message role |
| `history[].content` | Must not be empty | Message content is required |

---

## Common Query Examples

### User Authentication

#### Register New User

```python
# Using Supabase Python client
from supabase import create_client

supabase = create_client(supabase_url, supabase_key)

# Sign up
response = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure_password123"
})

user_id = response.user.id
access_token = response.session.access_token
```

#### Login User

```python
# Sign in
response = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "secure_password123"
})

user_id = response.user.id
access_token = response.session.access_token
```

---

### Academic Profile Operations

#### Create Academic Profile

```python
# Create profile (one-time, after user registration)
profile = supabase.table("academic").insert({
    "id": user_id,
    "grade": ["Bachelor"],
    "semester_type": "double",
    "semester": 3,
    "subject": ["computer science", "english"]
}).execute()
```

#### Get Academic Profile

```python
# Get user's academic profile
profile = supabase.table("academic").select("*").eq("id", user_id).single().execute()

print(f"Grade: {profile.data['grade']}")
print(f"Semester: {profile.data['semester']}")
print(f"Subjects: {profile.data['subject']}")
```

#### Update Academic Profile

```python
# Update semester
updated = supabase.table("academic").update({
    "semester": 4
}).eq("id", user_id).execute()
```

---

### Personalized Preferences Operations

#### Create Preferences

```python
# Create preferences (one-time, after questionnaire)
prefs = supabase.table("personalized").insert({
    "id": user_id,
    "prefs": {
        "detail_level": 0.7,
        "example_preference": 0.8,
        "analogy_preference": 0.6,
        "technical_language": 0.5,
        "structure_preference": 0.7,
        "visual_preference": 0.9,
        "learning_pace": "moderate",
        "prior_experience": "intermediate"
    }
}).execute()
```

#### Get Preferences

```python
# Get user's preferences
prefs = supabase.table("personalized").select("*").eq("id", user_id).single().execute()

print(f"Learning pace: {prefs.data['prefs']['learning_pace']}")
print(f"Detail level: {prefs.data['prefs']['detail_level']}")
```

#### Update Specific Preference Field

```python
# Update learning pace (partial JSONB update)
updated = supabase.table("personalized").update({
    "prefs": {
        **existing_prefs,  # Spread existing preferences
        "learning_pace": "fast"  # Update specific field
    }
}).eq("id", user_id).execute()
```

---

### Course Operations

#### Create Course

```python
# Create new course
course = supabase.table("courses").insert({
    "user_id": user_id,
    "name": "Machine Learning Fundamentals"
}).execute()

course_id = course.data[0]["id"]
```

#### List User's Courses

```python
# Get all courses for user (RLS automatically filters)
courses = supabase.table("courses").select("*").execute()

for course in courses.data:
    print(f"{course['name']} (created: {course['created_at']})")
```

#### Update Course Name

```python
# Update course name
updated = supabase.table("courses").update({
    "name": "Advanced Machine Learning"
}).eq("id", course_id).execute()
```

#### Delete Course

```python
# Delete course (cascades to materials and chat_history)
deleted = supabase.table("courses").delete().eq("id", course_id).execute()
```

---

### Materials Operations

#### Upload Material Metadata

```python
# After uploading file to Supabase Storage, save metadata
material = supabase.table("materials").insert({
    "course_id": course_id,
    "name": "Introduction to Neural Networks.pdf",
    "file_path": f"{user_id}/{course_id}/neural_networks.pdf",
    "file_type": "application/pdf",
    "file_size": 2048576  # 2MB in bytes
}).execute()

material_id = material.data[0]["id"]
```

#### List Course Materials

```python
# Get all materials for a course
materials = supabase.table("materials").select("*").eq("course_id", course_id).execute()

for material in materials.data:
    size_mb = material['file_size'] / (1024 * 1024)
    print(f"{material['name']} ({size_mb:.2f} MB)")
```

#### Delete Material

```python
# Delete material metadata (also delete from storage separately)
deleted = supabase.table("materials").delete().eq("id", material_id).execute()
```

---

### Chat History Operations

#### Create Chat Record

```python
# Create new chat with initial messages
chat = supabase.table("chat_history").insert({
    "course_id": course_id,
    "history": [
        {"role": "user", "content": "What is machine learning?"},
        {"role": "model", "content": "Machine learning is a subset of AI..."}
    ]
}).execute()

chat_id = chat.data[0]["id"]
```

#### Append Messages to Chat

```python
# Get existing chat
existing_chat = supabase.table("chat_history").select("*").eq("id", chat_id).single().execute()

# Append new messages
updated_history = existing_chat.data["history"] + [
    {"role": "user", "content": "Can you give an example?"},
    {"role": "model", "content": "Sure! Consider email spam detection..."}
]

# Update chat
updated = supabase.table("chat_history").update({
    "history": updated_history
}).eq("id", chat_id).execute()
```

#### Get Chat History for Course

```python
# Get all chat records for a course, ordered by creation time
chats = supabase.table("chat_history") \
    .select("*") \
    .eq("course_id", course_id) \
    .order("created_at", desc=False) \
    .execute()

for chat in chats.data:
    print(f"Chat {chat['id']}: {len(chat['history'])} messages")
```

---

### Advanced Queries

#### Find Users by Grade Level

```python
# Find all Bachelor students (requires service role or admin access)
students = supabase.table("academic") \
    .select("*") \
    .contains("grade", ["Bachelor"]) \
    .execute()
```

#### Query JSONB Preferences

```python
# Find users with fast learning pace (requires service role or admin access)
fast_learners = supabase.table("personalized") \
    .select("*") \
    .eq("prefs->>learning_pace", "fast") \
    .execute()
```

#### Vector Similarity Search

```python
# Find similar chat conversations using vector embeddings
from pgvector.psycopg2 import register_vector

# Assuming you have a query embedding
query_embedding = [0.1, 0.2, ...]  # 384-dimensional vector

# Find top 5 most similar chats
similar_chats = supabase.rpc("match_chat_history", {
    "query_embedding": query_embedding,
    "match_threshold": 0.7,
    "match_count": 5
}).execute()
```

---

## Migration Scripts

### Migration Files

All migration scripts are located in `python-backend/migrations/` and should be executed in order:

| File | Purpose | Requirements |
|------|---------|--------------|
| `001_enable_extensions.sql` | Enable PostgreSQL extensions | Requirement 1.4 |
| `002_create_tables.sql` | Create all tables with constraints and indexes | Requirements 3.1-7.5 |
| `003_create_rls_policies.sql` | Enable RLS and create security policies | Requirements 1.3, 8.4 |
| `004_rollback.sql` | Rollback script to drop all tables and policies | Requirement 8.5 |

### Running Migrations

#### Using Python Script

```bash
cd python-backend
python scripts/run_migrations.py
```

#### Manual Execution

```bash
# Connect to Supabase database
psql "postgresql://postgres:[password]@[project-ref].supabase.co:5432/postgres"

# Run migrations in order
\i migrations/001_enable_extensions.sql
\i migrations/002_create_tables.sql
\i migrations/003_create_rls_policies.sql
```

#### Using Supabase Dashboard

1. Navigate to SQL Editor in Supabase Dashboard
2. Copy contents of each migration file
3. Execute in order (001 → 002 → 003)

### Rollback Procedure

To rollback all changes:

```sql
-- Execute rollback script
\i migrations/004_rollback.sql
```

**⚠️ Warning**: Rollback will delete all data. Use with caution!

### Migration Best Practices

1. **Always backup** before running migrations in production
2. **Test migrations** on a staging environment first
3. **Run migrations in order** (001 → 002 → 003)
4. **Verify success** after each migration
5. **Keep rollback scripts** updated with schema changes
6. **Version control** all migration files
7. **Document changes** in migration file comments

---

## Data Types Reference

### PostgreSQL Data Types Used

| Type | Description | Example Usage |
|------|-------------|---------------|
| `UUID` | Universally unique identifier | Primary keys, foreign keys |
| `TEXT` | Variable-length string | Names, descriptions, file paths |
| `TEXT[]` | Array of text values | Grade levels, subjects |
| `INTEGER` | 4-byte integer | Semester numbers |
| `BIGINT` | 8-byte integer | File sizes in bytes |
| `JSONB` | Binary JSON data | Preferences, message history |
| `JSONB[]` | Array of JSONB objects | Chat message arrays |
| `VECTOR(n)` | Vector of n dimensions | Embeddings for similarity search |
| `TIMESTAMPTZ` | Timestamp with timezone | Creation and update times |

### Array Operations

```sql
-- Check if array contains value
WHERE grade @> ARRAY['Bachelor']

-- Check if array is subset
WHERE grade <@ ARRAY['Bachelor', 'Masters']

-- Array length
WHERE array_length(grade, 1) > 0
```

### JSONB Operations

```sql
-- Get field value
SELECT prefs->>'learning_pace' FROM personalized

-- Check if field exists
WHERE prefs ? 'detail_level'

-- Filter by field value
WHERE prefs->>'learning_pace' = 'fast'

-- Update specific field
UPDATE personalized SET prefs = jsonb_set(prefs, '{learning_pace}', '"fast"')
```

### Vector Operations

```sql
-- Cosine distance (for similarity)
ORDER BY embedding <=> query_vector

-- Euclidean distance
ORDER BY embedding <-> query_vector

-- Inner product
ORDER BY embedding <#> query_vector
```

---

## Security Considerations

### Authentication Security

- **Password Hashing**: Supabase automatically uses bcrypt for password hashing
- **JWT Tokens**: Access tokens expire after 1 hour (configurable)
- **Refresh Tokens**: Used to obtain new access tokens without re-authentication
- **Email Verification**: Recommended to enable in Supabase Auth settings

### Data Access Security

- **Row Level Security**: Enabled on all tables to enforce data isolation
- **Service Role Key**: Bypasses RLS - use only in backend, never expose to client
- **Anon Key**: Public key for client-side operations - RLS enforced
- **User Context**: RLS policies use `auth.uid()` to identify authenticated user

### API Security Best Practices

1. **Never expose service role key** in client-side code
2. **Validate all inputs** on backend before database operations
3. **Use parameterized queries** (Supabase client handles this)
4. **Implement rate limiting** on authentication endpoints
5. **Enable email verification** for production
6. **Rotate keys periodically** (service role, anon key)
7. **Monitor failed login attempts** for security threats
8. **Use HTTPS only** for all API communications

### Database Security

- **Foreign Key Constraints**: Prevent orphaned records
- **Check Constraints**: Enforce valid data values
- **Unique Constraints**: Prevent duplicate records
- **NOT NULL Constraints**: Ensure required fields are populated
- **CASCADE Deletion**: Automatically clean up dependent records

---

## Performance Optimization

### Indexing Strategy

- **Primary Keys**: Automatically indexed
- **Foreign Keys**: Indexed for join performance
- **Array Columns**: GIN indexes for containment queries
- **JSONB Columns**: GIN indexes for field queries
- **Vector Columns**: HNSW indexes for similarity search

### Query Optimization Tips

1. **Use indexes**: Ensure queries use indexed columns in WHERE clauses
2. **Limit results**: Use LIMIT for pagination
3. **Select specific columns**: Avoid `SELECT *` when possible
4. **Use connection pooling**: Reuse database connections
5. **Batch operations**: Insert/update multiple records in single query
6. **Monitor slow queries**: Use Supabase dashboard to identify bottlenecks

### Scaling Considerations

- **Vertical Scaling**: Upgrade Supabase plan for more resources
- **Read Replicas**: Use for read-heavy workloads (Supabase Pro+)
- **Connection Pooling**: Configure appropriate pool size
- **Caching**: Implement application-level caching for frequently accessed data
- **Archiving**: Move old data to separate tables or storage

---

## Monitoring and Maintenance

### Database Monitoring

**Supabase Dashboard Metrics**:
- Query performance and slow queries
- Database size and storage usage
- Connection pool utilization
- Error rates and failed queries
- API request volume

### Backup Strategy

**Supabase Automatic Backups**:
- Daily backups (retained for 7 days on Free plan)
- Point-in-time recovery (Pro plan and above)
- Manual backups via pg_dump

**Manual Backup Example**:

```bash
# Export entire database
pg_dump "postgresql://postgres:[password]@[project-ref].supabase.co:5432/postgres" > backup.sql

# Export specific table
pg_dump -t public.courses "postgresql://..." > courses_backup.sql
```

### Maintenance Tasks

**Regular Tasks**:
- Monitor storage usage and plan upgrades
- Review slow query logs and optimize
- Rotate API keys periodically
- Test backup restoration process
- Update PostgreSQL extensions
- Review and update RLS policies as needed

**Schema Evolution**:
- Create new numbered migration files for changes
- Test migrations on staging environment
- Always provide rollback scripts
- Document breaking changes
- Version API alongside schema changes

---

## Troubleshooting

### Common Issues

#### RLS Policy Blocking Queries

**Symptom**: Queries return empty results even though data exists

**Solution**:
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- View policies
SELECT * FROM pg_policies WHERE schemaname = 'public';

-- Test with service role (bypasses RLS)
-- Use service role key in backend
```

#### Foreign Key Constraint Violations

**Symptom**: Insert/update fails with foreign key error

**Solution**:
- Ensure referenced record exists before inserting
- Check CASCADE settings for deletions
- Verify user_id matches authenticated user

#### JSONB Query Not Using Index

**Symptom**: Slow queries on JSONB fields

**Solution**:
```sql
-- Ensure GIN index exists
CREATE INDEX IF NOT EXISTS idx_personalized_prefs ON personalized USING GIN (prefs);

-- Use proper JSONB operators
WHERE prefs->>'learning_pace' = 'fast'  -- Uses index
```

#### Vector Search Performance

**Symptom**: Slow similarity searches

**Solution**:
```sql
-- Ensure HNSW index exists
CREATE INDEX IF NOT EXISTS chat_history_embedding_idx 
    ON chat_history 
    USING hnsw (embedding vector_cosine_ops);

-- Adjust HNSW parameters for speed vs accuracy tradeoff
```

---

## Appendix

### Pydantic Models

The Python backend uses Pydantic models for request/response validation. See `python-backend/models/schemas.py` for complete definitions.

**Key Models**:
- `AcademicProfile` - Academic profile validation
- `UserPreferences` - Preferences validation
- `CourseCreate` / `CourseResponse` - Course operations
- `MaterialCreate` / `MaterialResponse` - Material operations
- `ChatRequest` / `ChatResponse` - Chat operations
- `SignupRequest` / `LoginRequest` - Authentication

### API Endpoints

Complete API documentation available in:
- `python-backend/API_ENDPOINTS.md` - Endpoint reference
- `python-backend/API_ROUTES_SUMMARY.md` - Route summary

### Additional Resources

- **Supabase Documentation**: https://supabase.com/docs
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **pgvector Documentation**: https://github.com/pgvector/pgvector
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

---

## Document Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024 | Initial database schema documentation | System |

---

**End of Database Schema Documentation**
