# API Reference - Registration Flow

## Base URL

**Development:** `http://localhost:8000/api`  
**Production:** `https://your-api-domain.com/api`

All endpoints are prefixed with `/api`.

## Authentication

Most endpoints require authentication via JWT Bearer token:

```http
Authorization: Bearer <access_token>
```

Tokens are obtained from the signup or login endpoints and must be included in the Authorization header for protected endpoints.

## Response Format

### Success Response

All successful responses return JSON with appropriate status codes:

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### Error Response

All error responses follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Authentication Endpoints

### POST /api/auth/signup

Create a new user account.

**Request:**
```http
POST /api/auth/signup
Content-Type: application/json

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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 400 | Email already exists | `{"detail": "A user with this email already exists"}` |
| 400 | Password too short | `{"detail": "Password must be at least 8 characters"}` |
| 422 | Validation error | `{"detail": "Invalid email format"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

**Validation Rules:**
- Email must be valid format
- Password must be at least 8 characters
- Email must not already exist in system

---

### POST /api/auth/login

Authenticate an existing user.

**Request:**
```http
POST /api/auth/login
Content-Type: application/json

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
    "created_at": "2025-12-02T10:30:00Z",
    "last_sign_in_at": "2025-12-02T15:45:00Z"
  }
}
```

**Error Responses:**

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid credentials | `{"detail": "Invalid email or password"}` |
| 422 | Validation error | `{"detail": "Email is required"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

### POST /api/auth/logout

Logout the current user and invalidate their session.

**Request:**
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Error Responses:**

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

### GET /api/auth/session

Get information about the current authenticated session.

**Request:**
```http
GET /api/auth/session
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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

### POST /api/auth/refresh

Refresh an expired access token using a refresh token.

**Request:**
```http
POST /api/auth/refresh
Content-Type: application/json

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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid refresh token | `{"detail": "Invalid or expired refresh token"}` |
| 422 | Missing refresh token | `{"detail": "Refresh token is required"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

## Academic Profile Endpoints

### POST /api/academic

Create an academic profile for the authenticated user.

**Request:**
```http
POST /api/academic
Authorization: Bearer <access_token>
Content-Type: application/json

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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 409 | Profile already exists | `{"detail": "Academic profile already exists. Use PUT to update."}` |
| 422 | Validation error | `{"detail": "Grade is required"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

**Validation Rules:**
- `grade`: Array of strings, required, at least one value
- `semester_type`: Must be "double" or "tri", required
- `semester`: Integer between 1-12, required
- `subject`: Array of strings, required, at least one value

---

### GET /api/academic

Retrieve the academic profile for the authenticated user.

**Request:**
```http
GET /api/academic
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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 404 | Profile not found | `{"detail": "Academic profile not found"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

### PUT /api/academic

Update the academic profile for the authenticated user.

**Request:**
```http
PUT /api/academic
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "grade": ["Masters"],
  "semester_type": "tri",
  "semester": 2,
  "subject": ["artificial intelligence", "machine learning", "data science"]
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "grade": ["Masters"],
  "semester_type": "tri",
  "semester": 2,
  "subject": ["artificial intelligence", "machine learning", "data science"],
  "created_at": "2025-12-02T10:35:00Z",
  "updated_at": "2025-12-02T11:20:00Z"
}
```

**Error Responses:**

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 404 | Profile not found | `{"detail": "Academic profile not found"}` |
| 422 | Validation error | `{"detail": "Semester must be between 1 and 12"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

## Preferences Endpoints

### POST /api/preferences

Create or update learning preferences for the authenticated user.

**Request:**
```http
POST /api/preferences
Authorization: Bearer <access_token>
Content-Type: application/json

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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 422 | Validation error | `{"detail": "detail_level must be between 0 and 1"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

**Validation Rules:**
- Numeric preferences (0-1 scale): `detail_level`, `example_preference`, `analogy_preference`, `technical_language`, `structure_preference`, `visual_preference`
- `learning_pace`: Must be "slow", "moderate", or "fast"
- `prior_experience`: Must be "beginner", "intermediate", "advanced", or "expert"

---

### GET /api/preferences

Retrieve learning preferences for the authenticated user.

**Request:**
```http
GET /api/preferences
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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 404 | Preferences not found | `{"detail": "Preferences not found"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

---

### PUT /api/preferences

Update learning preferences for the authenticated user.

**Request:**
```http
PUT /api/preferences
Authorization: Bearer <access_token>
Content-Type: application/json

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

| Status Code | Description | Example |
|-------------|-------------|---------|
| 401 | Invalid/expired token | `{"detail": "Invalid or expired authentication token"}` |
| 403 | No token provided | `{"detail": "Not authenticated"}` |
| 404 | Preferences not found | `{"detail": "Preferences not found"}` |
| 422 | Validation error | `{"detail": "learning_pace must be slow, moderate, or fast"}` |
| 500 | Server error | `{"detail": "An unexpected error occurred"}` |

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

## Rate Limiting

Authentication endpoints are rate-limited to prevent abuse:

- **Signup:** 5 requests per minute per IP
- **Login:** 10 requests per minute per IP
- **Refresh:** 20 requests per minute per IP

When rate limit is exceeded, the API returns:

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

**Status Code:** 429 Too Many Requests

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for the following origins:

- `http://localhost:5173` (Development)
- `http://localhost:8080` (Development)
- Production domain (configured via environment variable)

Allowed methods: GET, POST, PUT, DELETE, OPTIONS  
Allowed headers: Authorization, Content-Type

## Example Usage

### Complete Registration Flow

```javascript
// Step 1: Signup
const signupResponse = await fetch('http://localhost:8000/api/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePassword123'
  })
});

const { access_token, refresh_token, user } = await signupResponse.json();

// Store tokens
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);
localStorage.setItem('user', JSON.stringify(user));

// Step 2: Create Academic Profile
const academicResponse = await fetch('http://localhost:8000/api/academic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    grade: ['Bachelor'],
    semester_type: 'double',
    semester: 3,
    subject: ['computer science', 'mathematics']
  })
});

const academicProfile = await academicResponse.json();

// Step 3: Create Preferences
const preferencesResponse = await fetch('http://localhost:8000/api/preferences', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    detail_level: 0.7,
    example_preference: 0.8,
    analogy_preference: 0.6,
    technical_language: 0.5,
    structure_preference: 0.7,
    visual_preference: 0.9,
    learning_pace: 'moderate',
    prior_experience: 'intermediate'
  })
});

const preferences = await preferencesResponse.json();

// Registration complete!
console.log('Registration successful!');
```

### Handling Token Refresh

```javascript
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  // If token expired, refresh and retry
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    
    const refreshResponse = await fetch('http://localhost:8000/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (refreshResponse.ok) {
      const { access_token, refresh_token } = await refreshResponse.json();
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Retry original request with new token
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${access_token}`,
          'Content-Type': 'application/json'
        }
      });
    } else {
      // Refresh failed, logout user
      localStorage.clear();
      window.location.href = '/login';
      throw new Error('Session expired. Please login again.');
    }
  }
  
  return response;
}
```

## Related Documentation

- [Registration Flow](./REGISTRATION_FLOW.md) - Complete registration flow documentation
- [Environment Setup](./ENVIRONMENT_SETUP.md) - Environment configuration
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions
