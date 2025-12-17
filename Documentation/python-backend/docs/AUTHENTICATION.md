# Authentication Implementation Guide

This document describes the authentication system implemented for the StudyMate backend using Supabase Auth.

## Overview

The authentication system provides JWT-based authentication using Supabase Auth. It includes:

1. **Auth Service** (`services/auth_service.py`) - Core authentication utilities
2. **Auth Middleware** (`middleware/auth_middleware.py`) - Request-level authentication
3. **FastAPI Dependencies** - Easy-to-use route protection

## Components

### 1. Auth Service (`services/auth_service.py`)

The auth service provides the following utilities:

#### `AuthUser` Class
Represents an authenticated user with:
- `id`: User's UUID from Supabase
- `email`: User's email address
- `access_token`: JWT token for authenticated requests

#### `verify_jwt_token(token: str) -> Optional[dict]`
Verifies a JWT token using Supabase Auth and returns user data.

**Usage:**
```python
user_data = await verify_jwt_token(access_token)
# Returns: {"id": "uuid", "email": "user@example.com", "role": "authenticated"}
```

#### `get_user_from_token(token: str) -> AuthUser`
Extracts and validates user information from a JWT token.

**Usage:**
```python
user = await get_user_from_token(access_token)
print(f"User: {user.email}")
```

#### `get_current_user` (FastAPI Dependency)
FastAPI dependency for protected routes. Automatically extracts and validates the JWT token from the Authorization header.

**Usage:**
```python
@router.get("/protected")
async def protected_route(user: AuthUser = Depends(get_current_user)):
    return {"message": f"Hello {user.email}"}
```

#### `get_current_user_optional` (FastAPI Dependency)
Optional authentication dependency. Returns `None` if no token is provided or token is invalid.

**Usage:**
```python
@router.get("/flexible")
async def flexible_route(user: Optional[AuthUser] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user.email}"}
    else:
        return {"message": "Hello guest"}
```

### 2. Auth Middleware (`middleware/auth_middleware.py`)

Two middleware classes are provided:

#### `AuthMiddleware`
Enriches requests with user information but doesn't block unauthenticated requests.

**Features:**
- Extracts Bearer token from Authorization header
- Validates token using Supabase Auth
- Attaches user info to `request.state.user`
- Attaches token to `request.state.access_token`
- Allows unauthenticated requests to pass through

**Usage:**
```python
from middleware.auth_middleware import AuthMiddleware

app = FastAPI()
app.add_middleware(AuthMiddleware)

@app.get("/api/example")
async def example(request: Request):
    if request.state.user:
        user_id = request.state.user["id"]
        email = request.state.user["email"]
        # User is authenticated
    else:
        # User is not authenticated
```

#### `RequireAuthMiddleware`
Strict authentication middleware that blocks all unauthenticated requests.

**Features:**
- Requires valid JWT token for all requests
- Returns 401 for missing or invalid tokens
- Allows specific public paths (configurable)
- Attaches user info to request.state

**Public Paths (by default):**
- `/health`
- `/docs`
- `/redoc`
- `/openapi.json`
- `/api/auth/signup`
- `/api/auth/login`
- `/api/auth/refresh`

**Usage:**
```python
from middleware.auth_middleware import RequireAuthMiddleware

# Protect entire API
app = FastAPI()
app.add_middleware(RequireAuthMiddleware)

# Or protect specific router
protected_router = APIRouter()
protected_router.add_middleware(RequireAuthMiddleware)
```

## Implementation Examples

### Example 1: Protected Route

```python
from fastapi import APIRouter, Depends
from services.auth_service import get_current_user, AuthUser

router = APIRouter()

@router.get("/api/profile")
async def get_profile(user: AuthUser = Depends(get_current_user)):
    """Get user profile - requires authentication."""
    return {
        "user_id": user.id,
        "email": user.email
    }
```

### Example 2: Optional Authentication

```python
from fastapi import APIRouter, Depends
from services.auth_service import get_current_user_optional, AuthUser
from typing import Optional

router = APIRouter()

@router.get("/api/content")
async def get_content(user: Optional[AuthUser] = Depends(get_current_user_optional)):
    """Get content - personalized if authenticated."""
    if user:
        # Return personalized content
        return {"content": "personalized", "user": user.email}
    else:
        # Return generic content
        return {"content": "generic"}
```

### Example 3: Using Middleware State

```python
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/api/example")
async def example(request: Request):
    """Access user info from middleware."""
    if hasattr(request.state, 'user') and request.state.user:
        user = request.state.user
        return {
            "authenticated": True,
            "user_id": user["id"],
            "email": user["email"]
        }
    else:
        return {"authenticated": False}
```

### Example 4: Multiple Dependencies

```python
from fastapi import APIRouter, Depends
from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client

router = APIRouter()

@router.get("/api/courses")
async def get_courses(user: AuthUser = Depends(get_current_user)):
    """Get user's courses with RLS enforcement."""
    # Create user-specific Supabase client (enforces RLS)
    client = get_user_client(user.access_token)
    
    # Query will only return courses owned by this user
    response = client.table("courses").select("*").execute()
    
    return {"courses": response.data}
```

## Making Authenticated Requests

### From Frontend (JavaScript/TypeScript)

```javascript
// Get token from Supabase Auth
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Make authenticated request
const response = await fetch('/api/profile', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

### From Python

```python
import httpx

token = "your_jwt_token_here"
headers = {"Authorization": f"Bearer {token}"}

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/profile",
        headers=headers
    )
    data = response.json()
```

### From cURL

```bash
curl -X GET "http://localhost:8000/api/profile" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json"
```

## Error Responses

### 401 Unauthorized - Missing Token

```json
{
  "detail": "Missing authentication token"
}
```

### 401 Unauthorized - Invalid Token

```json
{
  "detail": "Invalid or expired authentication token"
}
```

### 401 Unauthorized - Expired Token

```json
{
  "detail": "Invalid or expired authentication token"
}
```

## Security Best Practices

1. **Always use HTTPS in production** - JWT tokens should never be transmitted over unencrypted connections

2. **Store tokens securely** - Use httpOnly cookies or secure storage mechanisms in the frontend

3. **Validate tokens on every request** - The auth service automatically validates token signature and expiration

4. **Use RLS with user clients** - When accessing Supabase data, use `get_user_client(token)` to enforce Row Level Security

5. **Don't log tokens** - The auth service is configured to not log token values

6. **Set appropriate token expiration** - Configure token expiration in Supabase Auth settings (default: 1 hour)

7. **Implement token refresh** - Use Supabase's refresh token mechanism for long-lived sessions

## Testing Authentication

### Manual Testing with Swagger UI

1. Start the FastAPI server: `uvicorn main:app --reload`
2. Visit `http://localhost:8000/docs`
3. Click "Authorize" button at the top
4. Enter your JWT token in the format: `Bearer your_token_here`
5. Test protected endpoints

### Testing with Example Routes

The `routers/example_protected.py` file contains example routes for testing:

- `GET /api/examples/public` - No auth required
- `GET /api/examples/protected` - Auth required
- `GET /api/examples/optional-auth` - Optional auth
- `GET /api/examples/user-info` - Returns user details
- `GET /api/examples/middleware-example` - Uses middleware state

To enable these routes, add to `main.py`:
```python
from routers.example_protected import router as example_router
app.include_router(example_router)
```

## Integration with Supabase Auth

The authentication system integrates seamlessly with Supabase Auth:

1. **User Registration** - Handled by Supabase Auth API
2. **User Login** - Returns JWT access token
3. **Token Verification** - Uses Supabase's `get_user()` method
4. **Token Refresh** - Handled by Supabase Auth API
5. **User Logout** - Handled by Supabase Auth API

See the `routers/auth.py` implementation (Task 7) for complete authentication endpoints.

## Troubleshooting

### "Invalid or expired authentication token"

**Causes:**
- Token has expired (default: 1 hour)
- Token signature is invalid
- Token was issued by different Supabase project
- Supabase service role key is incorrect

**Solutions:**
- Refresh the token using Supabase Auth
- Verify `SUPABASE_SERVICE_ROLE_KEY` in `.env`
- Check token expiration time in Supabase dashboard

### "Missing authentication token"

**Causes:**
- No Authorization header in request
- Authorization header doesn't start with "Bearer "
- Token is empty string

**Solutions:**
- Include `Authorization: Bearer <token>` header
- Verify token is being sent from frontend
- Check network tab in browser dev tools

### Middleware not attaching user info

**Causes:**
- Middleware not registered in `main.py`
- Middleware registered after routes
- Token validation failing silently

**Solutions:**
- Add `app.add_middleware(AuthMiddleware)` in `main.py`
- Register middleware before route registration
- Check server logs for validation errors

## Next Steps

After implementing authentication utilities (Task 6), the next tasks are:

- **Task 7**: Create authentication routes (`/api/auth/signup`, `/api/auth/login`, etc.)
- **Task 8**: Create protected API routes for database operations
- **Task 9**: Write property-based tests for authentication
- **Task 10**: Write unit tests for authentication endpoints

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT token debugger
