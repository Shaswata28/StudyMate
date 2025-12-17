# StudyMate Backend API Endpoints

## Authentication Endpoints

### POST /api/auth/signup
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2025-12-02T10:30:00Z",
    "email_confirmed_at": "2025-12-02T10:30:00Z"
  }
}
```

**Error Responses:**
- `400` - Email already exists: `{"detail": "A user with this email already exists"}`
- `400` - Password too short: `{"detail": "Password must be at least 8 characters"}`
- `422` - Validation error: `{"detail": "Invalid email format"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

### POST /api/auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "last_sign_in_at": "2025-12-02T15:45:00Z"
  }
}
```

**Error Responses:**
- `401` - Invalid credentials: `{"detail": "Invalid email or password"}`
- `422` - Validation error: `{"detail": "Email is required"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

### POST /api/auth/logout
Logout current user and invalidate session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Error Responses:**
- `401` - Invalid token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

### GET /api/auth/session
Get current session information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2025-12-02T10:30:00Z",
    "email_confirmed_at": "2025-12-02T10:30:00Z",
    "last_sign_in_at": "2025-12-02T15:45:00Z"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2025-12-02T16:45:00Z"
  }
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

### POST /api/auth/refresh
Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

**Error Responses:**
- `401` - Invalid refresh token: `{"detail": "Invalid or expired refresh token"}`
- `422` - Missing refresh token: `{"detail": "Refresh token is required"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

## Academic Profile Endpoints

### POST /api/academic
Create an academic profile for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "grade": ["Bachelor"],
  "semester_type": "double",
  "semester": 3,
  "subject": ["computer science", "mathematics"]
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "grade": ["Bachelor"],
  "semester_type": "double",
  "semester": 3,
  "subject": ["computer science", "mathematics"],
  "created_at": "2025-12-02T10:35:00Z",
  "updated_at": "2025-12-02T10:35:00Z"
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `409` - Profile exists: `{"detail": "Academic profile already exists. Use PUT to update."}`
- `422` - Validation error: `{"detail": "Grade is required"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

**Validation Rules:**
- `grade`: Array of strings, required, at least one value
- `semester_type`: Must be "double" or "tri", required
- `semester`: Integer between 1-12, required
- `subject`: Array of strings, required, at least one value

---

### GET /api/academic
Retrieve the academic profile for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "grade": ["Bachelor"],
  "semester_type": "double",
  "semester": 3,
  "subject": ["computer science", "mathematics"],
  "created_at": "2025-12-02T10:35:00Z",
  "updated_at": "2025-12-02T10:35:00Z"
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `404` - Profile not found: `{"detail": "Academic profile not found"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

### PUT /api/academic
Update the academic profile for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "grade": ["Masters"],
  "semester_type": "tri",
  "semester": 2,
  "subject": ["artificial intelligence", "machine learning"]
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "grade": ["Masters"],
  "semester_type": "tri",
  "semester": 2,
  "subject": ["artificial intelligence", "machine learning"],
  "created_at": "2025-12-02T10:35:00Z",
  "updated_at": "2025-12-02T11:20:00Z"
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `404` - Profile not found: `{"detail": "Academic profile not found"}`
- `422` - Validation error: `{"detail": "Semester must be between 1 and 12"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

## Preferences Endpoints

### POST /api/preferences
Create or update learning preferences for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "detail_level": 0.7,
  "example_preference": 0.8,
  "analogy_preference": 0.6,
  "technical_language": 0.5,
  "structure_preference": 0.7,
  "visual_preference": 0.9,
  "learning_pace": "moderate",
  "prior_experience": "intermediate"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "prefs": {
    "detail_level": 0.7,
    "example_preference": 0.8,
    "analogy_preference": 0.6,
    "technical_language": 0.5,
    "structure_preference": 0.7,
    "visual_preference": 0.9,
    "learning_pace": "moderate",
    "prior_experience": "intermediate"
  },
  "created_at": "2025-12-02T10:40:00Z",
  "updated_at": "2025-12-02T10:40:00Z"
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `422` - Validation error: `{"detail": "detail_level must be between 0 and 1"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

**Validation Rules:**
- Numeric preferences (0-1 scale): `detail_level`, `example_preference`, `analogy_preference`, `technical_language`, `structure_preference`, `visual_preference`
- `learning_pace`: Must be "slow", "moderate", or "fast"
- `prior_experience`: Must be "beginner", "intermediate", "advanced", or "expert"

---

### GET /api/preferences
Retrieve learning preferences for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "prefs": {
    "detail_level": 0.7,
    "example_preference": 0.8,
    "analogy_preference": 0.6,
    "technical_language": 0.5,
    "structure_preference": 0.7,
    "visual_preference": 0.9,
    "learning_pace": "moderate",
    "prior_experience": "intermediate"
  },
  "created_at": "2025-12-02T10:40:00Z",
  "updated_at": "2025-12-02T10:40:00Z"
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `404` - Preferences not found: `{"detail": "Preferences not found"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

### PUT /api/preferences
Update learning preferences for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "detail_level": 0.9,
  "example_preference": 0.7,
  "analogy_preference": 0.8,
  "technical_language": 0.6,
  "structure_preference": 0.8,
  "visual_preference": 0.5,
  "learning_pace": "fast",
  "prior_experience": "advanced"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "prefs": {
    "detail_level": 0.9,
    "example_preference": 0.7,
    "analogy_preference": 0.8,
    "technical_language": 0.6,
    "structure_preference": 0.8,
    "visual_preference": 0.5,
    "learning_pace": "fast",
    "prior_experience": "advanced"
  },
  "created_at": "2025-12-02T10:40:00Z",
  "updated_at": "2025-12-02T11:25:00Z"
}
```

**Error Responses:**
- `401` - Invalid/expired token: `{"detail": "Invalid or expired authentication token"}`
- `403` - No token: `{"detail": "Not authenticated"}`
- `404` - Preferences not found: `{"detail": "Preferences not found"}`
- `422` - Validation error: `{"detail": "learning_pace must be slow, moderate, or fast"}`
- `500` - Server error: `{"detail": "An unexpected error occurred"}`

---

## Course Management Endpoints

### POST /api/courses
Create a new course.
- **Headers**: `Authorization: Bearer <token>`
- **Body**: `{ "name": "Biology 101" }`
- **Response**: Course object with ID

### GET /api/courses
List all user's courses.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Array of course objects

### GET /api/courses/{course_id}
Get specific course details.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Course object

### PUT /api/courses/{course_id}
Update course name.
- **Headers**: `Authorization: Bearer <token>`
- **Body**: `{ "name": "Updated Course Name" }`
- **Response**: Updated course object

### DELETE /api/courses/{course_id}
Delete a course (cascades to materials and chat history).
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Success message

---

## Materials Management Endpoints

### POST /api/courses/{course_id}/materials
Upload a material file.
- **Headers**: `Authorization: Bearer <token>`
- **Body**: Multipart form data with file
- **Response**: Material metadata object

### GET /api/courses/{course_id}/materials
List all materials for a course.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Array of material objects

### GET /api/materials/{material_id}
Get material metadata.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Material object

### GET /api/materials/{material_id}/download
Download a material file.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: File stream

### DELETE /api/materials/{material_id}
Delete a material and its file.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Success message

---

## Chat Endpoint

### POST /api/chat
Send a message to the AI.
- **Body**:
```json
{
  "message": "Explain photosynthesis",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "model", "content": "Hi! How can I help?" }
  ],
  "attachments": []
}
```
- **Response**: AI response with timestamp

---

## Health Check

### GET /health
Check if the API is running.
- **Response**: `{ "status": "healthy", "service": "studymate-ai-chat" }`

---

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE, or POST (non-creation) |
| 201 | Created | Successful POST that creates a resource |
| 400 | Bad Request | Validation error or business logic error |
| 401 | Unauthorized | Invalid or expired authentication token |
| 403 | Forbidden | No authentication token provided |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate profile) |
| 422 | Unprocessable Entity | Request body validation failed |
| 500 | Internal Server Error | Unexpected server error |

---

## Error Response Format

All error responses follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Messages

**Authentication Errors:**
- `"Invalid or expired authentication token"` - Token is invalid or expired
- `"Not authenticated"` - No token provided
- `"Invalid email or password"` - Login credentials are incorrect

**Validation Errors:**
- `"A user with this email already exists"` - Email already registered
- `"Password must be at least 8 characters"` - Password too short
- `"Grade is required"` - Missing required field
- `"Semester must be between 1 and 12"` - Invalid value

**Conflict Errors:**
- `"Academic profile already exists. Use PUT to update."` - Profile already created
- `"Resource already exists"` - Duplicate resource

**Not Found Errors:**
- `"Academic profile not found"` - Profile doesn't exist
- `"Preferences not found"` - Preferences don't exist

**Server Errors:**
- `"An unexpected error occurred"` - Generic server error

---

## Rate Limiting

Authentication endpoints are rate-limited to prevent abuse:

- **Signup:** 5 requests per minute per IP
- **Login:** 10 requests per minute per IP
- **Refresh:** 20 requests per minute per IP

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```
**Status Code:** 429 Too Many Requests

---

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for:

- `http://localhost:5173` (Development)
- `http://localhost:8080` (Development)
- Production domain (configured via environment variable)

**Allowed Methods:** GET, POST, PUT, DELETE, OPTIONS  
**Allowed Headers:** Authorization, Content-Type

---

## Complete Registration Flow Example

```bash
# Step 1: Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}'

# Response includes access_token, refresh_token, user

# Step 2: Create Academic Profile
curl -X POST http://localhost:8000/api/academic \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "grade": ["Bachelor"],
    "semester_type": "double",
    "semester": 3,
    "subject": ["computer science", "mathematics"]
  }'

# Step 3: Create Preferences
curl -X POST http://localhost:8000/api/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "detail_level": 0.7,
    "example_preference": 0.8,
    "analogy_preference": 0.6,
    "technical_language": 0.5,
    "structure_preference": 0.7,
    "visual_preference": 0.9,
    "learning_pace": "moderate",
    "prior_experience": "intermediate"
  }'
```

---

## Database Tables Alignment

✅ **academic** - Managed by `/api/academic`
✅ **personalized** - Managed by `/api/preferences`
✅ **courses** - Managed by `/api/courses/*`
✅ **materials** - Managed by `/api/courses/{id}/materials` and `/api/materials/*`
✅ **chat_history** - Ready for integration (currently chat doesn't persist)
✅ **Storage bucket** - Integrated with materials upload/download

---

## Additional Documentation

- [Registration Flow Guide](../docs/REGISTRATION_FLOW.md) - Complete registration flow documentation
- [API Reference](../docs/API_REFERENCE.md) - Detailed API reference with examples
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Environment Setup](../docs/ENVIRONMENT_SETUP.md) - Environment configuration

---

## Next Steps for Full Integration

1. **Chat History Persistence**: Modify `/api/chat` to save conversations to `chat_history` table
2. **Vector Embeddings**: Add embedding generation service for RAG functionality
3. **Semantic Search**: Implement vector similarity search for context retrieval
4. **Frontend Integration**: Connect React components to these endpoints
