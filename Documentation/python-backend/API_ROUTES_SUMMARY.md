# API Routes Summary

This document provides an overview of all API routes implemented for the Supabase database integration.

## Authentication Routes (`/api/auth`)

Handled by `routers/auth.py`:

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/session` - Get current session
- `POST /api/auth/refresh` - Refresh access token

## Academic Profile Routes (`/api/academic`)

Handled by `routers/academic.py`:

- `GET /api/academic` - Get user's academic profile
- `POST /api/academic` - Create academic profile
- `PUT /api/academic` - Update academic profile

**Requirements**: 3.1, 3.3, 3.4

## Preferences Routes (`/api/preferences`)

Handled by `routers/preferences.py`:

- `GET /api/preferences` - Get user's learning preferences
- `POST /api/preferences` - Create preferences
- `PUT /api/preferences` - Update preferences

**Requirements**: 4.1, 4.2, 4.3

## Course Management Routes (`/api/courses`)

Handled by `routers/courses.py`:

- `GET /api/courses` - List user's courses
- `POST /api/courses` - Create new course
- `GET /api/courses/{id}` - Get course details
- `PUT /api/courses/{id}` - Update course
- `DELETE /api/courses/{id}` - Delete course

**Requirements**: 5.1, 5.3, 5.4, 5.5

## Materials Management Routes

Handled by `routers/materials.py`:

- `GET /api/courses/{course_id}/materials` - List course materials
- `POST /api/courses/{course_id}/materials` - Upload material
- `GET /api/materials/{id}` - Get material details
- `GET /api/materials/{id}/download` - Download material file
- `DELETE /api/materials/{id}` - Delete material

**Requirements**: 6.1, 6.4, 6.5

## Chat Routes

Handled by `routers/chat.py`:

### Legacy Chat Endpoint
- `POST /api/chat` - Send message to AI (no persistence)

### Supabase-Integrated Chat Endpoints
- `GET /api/courses/{course_id}/chat` - Get chat history from Supabase
- `POST /api/courses/{course_id}/chat` - Save chat message to Supabase and get AI response

**Requirements**: 7.1, 7.2, 7.4

## Legacy Profile Routes (`/api/profile`)

Handled by `routers/profile.py` (kept for backward compatibility):

- `GET /api/profile/academic` - Get academic profile
- `POST /api/profile/academic` - Create/update academic profile
- `GET /api/profile/preferences` - Get preferences
- `POST /api/profile/preferences` - Create/update preferences

## Authentication

All routes except `/api/auth/*` and `/api/chat` (legacy) require authentication via JWT Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

The token is obtained from the login or signup endpoints and must be included in all authenticated requests.

## Row Level Security (RLS)

All database operations respect Supabase Row Level Security policies:

- Users can only access their own academic profiles and preferences
- Users can only access courses they own
- Users can only access materials and chat history for courses they own

The RLS policies are enforced automatically when using the user's JWT token with the Supabase client.

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists (for POST operations)
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - External service (Gemini AI) error

Error responses include a JSON body with error details:

```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Chat endpoints are rate-limited to prevent abuse. The default limit is configured in the environment variables:

- `RATE_LIMIT_REQUESTS` - Number of requests allowed
- `RATE_LIMIT_WINDOW` - Time window in seconds

When rate limit is exceeded, the API returns `429 Too Many Requests`.
