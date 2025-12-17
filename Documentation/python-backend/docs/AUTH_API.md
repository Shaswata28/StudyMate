# Authentication API Documentation

This document describes the authentication endpoints available in the StudyMate API.

## Base URL

All authentication endpoints are prefixed with `/api/auth`.

## Endpoints

### 1. User Registration (Signup)

**Endpoint:** `POST /api/auth/signup`

**Description:** Register a new user with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "email_confirmed_at": null
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request or user already exists
- `500 Internal Server Error`: Server error

---

### 2. User Login

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate a user with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "email_confirmed_at": "2024-01-01T00:05:00Z",
    "last_sign_in_at": "2024-01-01T12:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid email or password
- `500 Internal Server Error`: Server error

---

### 3. User Logout

**Endpoint:** `POST /api/auth/logout`

**Description:** Log out the current user and invalidate their session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated or invalid token
- `500 Internal Server Error`: Server error

---

### 4. Get Current Session

**Endpoint:** `GET /api/auth/session`

**Description:** Get information about the current user session. This can be used to verify if a token is still valid.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "email_confirmed_at": "2024-01-01T00:05:00Z",
    "last_sign_in_at": "2024-01-01T12:00:00Z"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated, session expired, or invalid token
- `500 Internal Server Error`: Server error

---

### 5. Refresh Access Token

**Endpoint:** `POST /api/auth/refresh`

**Description:** Obtain a new access token using a refresh token. Use this when the access token expires.

**Request Body:**
```json
{
  "refresh_token": "your-refresh-token-here"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "new_refresh_token_here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "email_confirmed_at": "2024-01-01T00:05:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
- `500 Internal Server Error`: Server error

---

## Authentication Flow

### Initial Registration/Login

1. User registers via `POST /api/auth/signup` or logs in via `POST /api/auth/login`
2. Server returns `access_token` and `refresh_token`
3. Client stores both tokens securely
4. Client includes `access_token` in `Authorization: Bearer <token>` header for protected endpoints

### Token Refresh

1. When `access_token` expires (typically after 1 hour), protected endpoints return `401 Unauthorized`
2. Client calls `POST /api/auth/refresh` with the `refresh_token`
3. Server returns new `access_token` and `refresh_token`
4. Client updates stored tokens and retries the original request

### Logout

1. Client calls `POST /api/auth/logout` with current `access_token`
2. Server invalidates the session
3. Client discards both `access_token` and `refresh_token`

---

## Using Protected Endpoints

To access protected endpoints (like user data, courses, materials, etc.), include the access token in the Authorization header:

```bash
curl -X GET https://api.example.com/api/courses \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully (signup)
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication failed or token invalid/expired
- `500 Internal Server Error`: Server-side error

---

## Security Notes

1. **HTTPS Only**: Always use HTTPS in production to protect tokens in transit
2. **Token Storage**: Store tokens securely (e.g., httpOnly cookies or secure storage)
3. **Token Expiration**: Access tokens expire after 1 hour by default
4. **Refresh Tokens**: Refresh tokens have longer expiration but should still be rotated
5. **Password Requirements**: Minimum 8 characters required
6. **Email Verification**: Email confirmation may be required depending on Supabase settings

---

## Example: Complete Authentication Flow (JavaScript)

```javascript
// 1. Register a new user
async function signup(email, password) {
  const response = await fetch('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) {
    throw new Error('Signup failed');
  }
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data;
}

// 2. Login existing user
async function login(email, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data;
}

// 3. Make authenticated request
async function fetchProtectedData() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/courses', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Token expired, try to refresh
    await refreshToken();
    return fetchProtectedData(); // Retry
  }
  
  return response.json();
}

// 4. Refresh token
async function refreshToken() {
  const refresh_token = localStorage.getItem('refresh_token');
  
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  
  if (!response.ok) {
    // Refresh failed, redirect to login
    window.location.href = '/login';
    return;
  }
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}

// 5. Logout
async function logout() {
  const token = localStorage.getItem('access_token');
  
  await fetch('/api/auth/logout', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}
```

---

## Testing with cURL

```bash
# Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Get session (replace TOKEN with actual access token)
curl -X GET http://localhost:8000/api/auth/session \
  -H "Authorization: Bearer TOKEN"

# Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"REFRESH_TOKEN"}'
```
