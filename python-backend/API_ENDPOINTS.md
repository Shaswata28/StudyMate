# StudyMate Backend API Endpoints

## Authentication Endpoints

### POST /api/auth/signup
Register a new user.
- **Body**: `{ "email": "user@example.com", "password": "password123" }`
- **Response**: Access token, refresh token, user info

### POST /api/auth/login
Login with email and password.
- **Body**: `{ "email": "user@example.com", "password": "password123" }`
- **Response**: Access token, refresh token, user info

### POST /api/auth/logout
Logout current user.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Success message

### GET /api/auth/session
Get current session information.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: User and session info

### POST /api/auth/refresh
Refresh access token.
- **Body**: `{ "refresh_token": "..." }`
- **Response**: New access token and refresh token

---

## Profile Endpoints

### POST /api/profile/academic
Create or update academic profile.
- **Headers**: `Authorization: Bearer <token>`
- **Body**: 
```json
{
  "grade": ["Bachelor"],
  "semester_type": "double",
  "semester": 3,
  "subject": ["computer science", "english"]
}
```
- **Response**: Success message

### GET /api/profile/academic
Get user's academic profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Academic profile data

### POST /api/profile/preferences
Create or update learning preferences.
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
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
- **Response**: Success message

### GET /api/profile/preferences
Get user's learning preferences.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Preferences data

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

## Database Tables Alignment

✅ **academic** - Managed by `/api/profile/academic`
✅ **personalized** - Managed by `/api/profile/preferences`
✅ **courses** - Managed by `/api/courses/*`
✅ **materials** - Managed by `/api/courses/{id}/materials` and `/api/materials/*`
✅ **chat_history** - Ready for integration (currently chat doesn't persist)
✅ **Storage bucket** - Integrated with materials upload/download

---

## Next Steps for Full Integration

1. **Chat History Persistence**: Modify `/api/chat` to save conversations to `chat_history` table
2. **Vector Embeddings**: Add embedding generation service for RAG functionality
3. **Semantic Search**: Implement vector similarity search for context retrieval
4. **Frontend Integration**: Connect React components to these endpoints
