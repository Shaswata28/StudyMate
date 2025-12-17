# Backend-Database Alignment Analysis

## Database Schema (from COMPLETE_SETUP.sql)

### Tables Created:
1. **academic** - User academic profiles
   - Columns: id (UUID), grade (TEXT[]), semester_type (TEXT), semester (INTEGER), subject (TEXT[])
   
2. **personalized** - User learning preferences
   - Columns: id (UUID), prefs (JSONB)
   
3. **courses** - Course containers
   - Columns: id (UUID), user_id (UUID), name (TEXT)
   
4. **materials** - File metadata
   - Columns: id (UUID), course_id (UUID), name (TEXT), file_path (TEXT), file_type (TEXT), file_size (BIGINT)
   
5. **chat_history** - Conversation logs with embeddings
   - Columns: id (UUID), course_id (UUID), history (JSONB[]), embedding (VECTOR(384))

### Storage:
- **course-materials** bucket (50MB limit, private)

## Backend Status

### ✅ COMPLETE:
1. **Authentication** - Fully implemented
   - `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/session`, `/api/auth/refresh`
   - Schemas: SignupRequest, LoginRequest, AuthResponse, RefreshTokenRequest, SessionResponse
   
2. **Chat** - Gemini integration working
   - `/api/chat` endpoint with rate limiting
   - Schemas: ChatRequest, ChatResponse with file attachments

3. **Pydantic Schemas** - Defined but not used in routes yet
   - AcademicProfile, UserPreferences, CourseCreate, CourseResponse, MaterialCreate, MaterialResponse

4. **Constants** - All validation rules defined
   - VALID_GRADES, VALID_SUBJECTS, VALID_SEMESTER_TYPES, etc.

5. **Supabase Client** - Properly configured
   - Admin client, user client factory, anonymous client

### ❌ MISSING - Database CRUD Operations:

#### 1. Academic Profile Routes (NOT IMPLEMENTED)
- `POST /api/profile/academic` - Create/update academic profile
- `GET /api/profile/academic` - Get user's academic profile

#### 2. User Preferences Routes (NOT IMPLEMENTED)
- `POST /api/profile/preferences` - Create/update preferences
- `GET /api/profile/preferences` - Get user's preferences

#### 3. Course Management Routes (NOT IMPLEMENTED)
- `POST /api/courses` - Create new course
- `GET /api/courses` - List user's courses
- `GET /api/courses/{course_id}` - Get specific course
- `PUT /api/courses/{course_id}` - Update course name
- `DELETE /api/courses/{course_id}` - Delete course

#### 4. Materials Management Routes (NOT IMPLEMENTED)
- `POST /api/courses/{course_id}/materials` - Upload material
- `GET /api/courses/{course_id}/materials` - List course materials
- `GET /api/materials/{material_id}` - Get material metadata
- `GET /api/materials/{material_id}/download` - Download file
- `DELETE /api/materials/{material_id}` - Delete material

#### 5. Chat History Routes (NOT IMPLEMENTED)
- `POST /api/courses/{course_id}/chat` - Save chat conversation
- `GET /api/courses/{course_id}/chat` - Get chat history
- `GET /api/courses/{course_id}/chat/search` - Vector similarity search

## Recommendations

### Priority 1: User Profile Routes
Create `python-backend/routers/profile.py` with academic and preferences endpoints.

### Priority 2: Course Management Routes
Create `python-backend/routers/courses.py` with full CRUD operations.

### Priority 3: Materials Management Routes
Create `python-backend/routers/materials.py` with file upload/download integration.

### Priority 4: Chat History Routes
Enhance `python-backend/routers/chat.py` to save conversations to database.

### Priority 5: Vector Search Service
Create `python-backend/services/embedding_service.py` for RAG functionality.

## Next Steps

1. Implement profile routes (academic + preferences)
2. Implement course CRUD routes
3. Implement materials upload/download routes
4. Add chat history persistence
5. Add vector embedding generation and search
