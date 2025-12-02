# Registration Flow Documentation

## Overview

The StudyMate registration system implements a three-step user onboarding process that collects security credentials, academic information, and learning preferences. The system uses JWT-based authentication with Supabase as the backend provider.

## Registration Steps

### Step 1: Security Credentials
Users provide basic account information:
- Full name
- Email address
- Password (minimum 8 characters)
- Terms and conditions acceptance

### Step 2: Academic Profile
Users provide educational context:
- Grade level (e.g., Bachelor, Masters, PhD)
- Semester type (Double or Tri)
- Current semester number
- Subject areas of study

### Step 3: Learning Preferences (Onboarding)
Users customize their learning experience:
- Detail level preference (0-1 scale)
- Example preference (0-1 scale)
- Analogy preference (0-1 scale)
- Technical language preference (0-1 scale)
- Structure preference (0-1 scale)
- Visual preference (0-1 scale)
- Learning pace (slow, moderate, fast)
- Prior experience level (beginner, intermediate, advanced, expert)

## Architecture

### Frontend Components

**Location:** `client/pages/Signup.tsx`

The Signup component manages the first two steps of registration:

```typescript
// Step 1: Security credentials
const handleStep1Submit = async () => {
  // Validate inputs
  const errors = validateStep1();
  if (Object.keys(errors).length > 0) return;
  
  // Call signup API
  const response = await signup({ email, password });
  
  // Store tokens and proceed to step 2
  setStep(2);
};

// Step 2: Academic profile
const handleStep2Submit = async () => {
  // Validate inputs
  const errors = validateStep2();
  if (Object.keys(errors).length > 0) return;
  
  // Call academic profile API
  await saveAcademicProfile({ grade, semester_type, semester, subject });
  
  // Navigate to onboarding
  navigate('/onboarding');
};
```

**Location:** `client/pages/Onboarding.tsx`

The Onboarding component manages step 3 (preferences).

### Authentication Service

**Location:** `client/lib/auth.ts`

The auth service handles all API communication and token management:

```typescript
class AuthService {
  // Step 1: Create account
  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    const authData = await response.json();
    this.setTokens(authData); // Store in localStorage
    return authData;
  }
  
  // Step 2: Save academic profile
  async saveAcademicProfile(profile: AcademicProfile): Promise<void> {
    await this.fetchWithAuth(`${API_BASE_URL}/academic`, {
      method: 'POST',
      body: JSON.stringify(profile)
    });
  }
  
  // Step 3: Save preferences
  async savePreferences(prefs: UserPreferences): Promise<void> {
    await this.fetchWithAuth(`${API_BASE_URL}/preferences`, {
      method: 'POST',
      body: JSON.stringify(prefs)
    });
  }
  
  // Authenticated request wrapper
  private async fetchWithAuth(url: string, options: RequestInit) {
    const token = this.getAccessToken();
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    // Handle token expiration
    if (response.status === 401) {
      await this.refreshToken();
      // Retry request with new token
      return this.fetchWithAuth(url, options);
    }
    
    return response;
  }
}
```

### Backend Endpoints

#### Authentication Router
**Location:** `python-backend/routers/auth.py`

Handles user account creation and authentication:

```python
@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(request: SignupRequest):
    """Create a new user account"""
    # Create user in Supabase Auth
    response = supabase.auth.admin.create_user({
        "email": request.email,
        "password": request.password,
        "email_confirm": True  # Auto-confirm for development
    })
    
    # Return tokens and user info
    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
        "token_type": "bearer",
        "expires_in": response.session.expires_in,
        "user": response.user
    }
```

#### Academic Profile Router
**Location:** `python-backend/routers/academic.py`

Manages academic profile data:

```python
@router.post("", status_code=201)
async def create_academic_profile(
    profile: AcademicProfile,
    current_user: AuthUser = Depends(get_current_user)
):
    """Create academic profile for authenticated user"""
    # Check for existing profile
    existing = supabase.table("academic").select("*").eq("id", current_user.id).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Academic profile already exists")
    
    # Insert profile
    result = supabase.table("academic").insert({
        "id": current_user.id,
        "grade": profile.grade,
        "semester_type": profile.semester_type,
        "semester": profile.semester,
        "subject": profile.subject
    }).execute()
    
    return result.data[0]
```

#### Preferences Router
**Location:** `python-backend/routers/preferences.py`

Manages learning preferences:

```python
@router.post("", status_code=201)
async def create_preferences(
    preferences: UserPreferences,
    current_user: AuthUser = Depends(get_current_user)
):
    """Create or update user preferences"""
    # Store as JSONB
    result = supabase.table("personalized").upsert({
        "id": current_user.id,
        "prefs": preferences.dict()
    }).execute()
    
    return result.data[0]
```

## Data Flow

### Complete Registration Sequence

```
User → Frontend (Step 1) → POST /api/auth/signup → Supabase Auth
                                                   ↓
                                            Create User
                                                   ↓
                                            Return Tokens
                                                   ↓
Frontend ← Store in localStorage ←─────────────────┘
   ↓
Frontend (Step 2) → POST /api/academic → Verify JWT → Insert into academic table
                                                              ↓
Frontend ← Success ←──────────────────────────────────────────┘
   ↓
Navigate to /onboarding
   ↓
Frontend (Step 3) → POST /api/preferences → Verify JWT → Upsert into personalized table
                                                                 ↓
Frontend ← Success ←─────────────────────────────────────────────┘
   ↓
Navigate to /dashboard
```

### Token Management

**Storage:**
- Access token: `localStorage.getItem('access_token')`
- Refresh token: `localStorage.getItem('refresh_token')`
- User info: `localStorage.getItem('user')`

**Automatic Refresh:**
```typescript
// When API returns 401
if (response.status === 401) {
  // Attempt to refresh token
  const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    body: JSON.stringify({ refresh_token: getRefreshToken() })
  });
  
  if (refreshResponse.ok) {
    const newTokens = await refreshResponse.json();
    setTokens(newTokens);
    // Retry original request
    return fetchWithAuth(originalUrl, originalOptions);
  } else {
    // Refresh failed, logout user
    clearTokens();
    navigate('/login');
  }
}
```

## Database Schema

### auth.users (Managed by Supabase)
```sql
CREATE TABLE auth.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  encrypted_password TEXT NOT NULL,
  email_confirmed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_sign_in_at TIMESTAMPTZ
);
```

### public.academic
```sql
CREATE TABLE public.academic (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  grade TEXT[] NOT NULL,
  semester_type TEXT NOT NULL CHECK (semester_type IN ('double', 'tri')),
  semester INTEGER NOT NULL,
  subject TEXT[] NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### public.personalized
```sql
CREATE TABLE public.personalized (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  prefs JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Error Handling

### Frontend Error Display

All errors are displayed using toast notifications:

```typescript
import { toast } from "@/hooks/use-toast";

try {
  await signup({ email, password });
} catch (error) {
  // Extract error message from response
  const message = error.detail || error.message || "An error occurred";
  
  toast({
    title: "Registration Failed",
    description: message,
    variant: "destructive"
  });
}
```

### Common Error Scenarios

| Error | Status Code | Message | User Action |
|-------|-------------|---------|-------------|
| Duplicate email | 400 | "A user with this email already exists" | Use different email or login |
| Weak password | 400 | "Password must be at least 8 characters" | Use stronger password |
| Invalid token | 401 | "Invalid or expired authentication token" | Re-login |
| Missing fields | 422 | "Field X is required" | Fill all required fields |
| Server error | 500 | "An unexpected error occurred" | Try again later |

### Backend Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message here"
}
```

Example error handling in backend:

```python
try:
    # Attempt operation
    result = supabase.table("academic").insert(data).execute()
except Exception as e:
    if "already exists" in str(e):
        raise HTTPException(status_code=409, detail="Academic profile already exists")
    else:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
```

## Validation Rules

### Step 1: Security Credentials

**Email:**
- Must be valid email format
- Must not already exist in system
- Example: `user@example.com`

**Password:**
- Minimum 8 characters
- Must match confirmation password
- Displayed with strength indicator

**Name:**
- Required field
- Minimum 2 characters

**Terms:**
- Must be accepted to proceed

### Step 2: Academic Profile

**Grade:**
- Required field
- Array of strings
- Valid values: Bachelor, Masters, PhD, High School, etc.

**Semester Type:**
- Required field
- Must be either "double" or "tri"

**Semester:**
- Required field
- Integer between 1 and 12

**Subject:**
- Required field
- Array of strings
- At least one subject must be selected

### Step 3: Preferences

**Numeric Preferences (0-1 scale):**
- detail_level
- example_preference
- analogy_preference
- technical_language
- structure_preference
- visual_preference

**Learning Pace:**
- Must be one of: "slow", "moderate", "fast"

**Prior Experience:**
- Must be one of: "beginner", "intermediate", "advanced", "expert"

## Testing

### Manual Testing Checklist

- [ ] Complete registration with valid data
- [ ] Test with invalid email format
- [ ] Test with password < 8 characters
- [ ] Test with mismatched passwords
- [ ] Test with duplicate email
- [ ] Test with missing required fields
- [ ] Test browser refresh during registration
- [ ] Test back button navigation
- [ ] Verify tokens stored in localStorage
- [ ] Verify data persists in database
- [ ] Test logout and re-login

### Automated Tests

**Frontend Tests:**
- `client/lib/auth.spec.ts` - Auth service unit tests
- `client/lib/registration-flow.e2e.spec.ts` - End-to-end flow tests

**Backend Tests:**
- `python-backend/test_auth_endpoints.py` - Authentication endpoint tests
- `python-backend/test_academic_endpoints.py` - Academic profile tests
- `python-backend/test_preferences_endpoints.py` - Preferences tests

Run all tests:
```bash
# Frontend tests
pnpm test

# Backend tests
cd python-backend
python test_auth_endpoints.py
python test_academic_endpoints.py
python test_preferences_endpoints.py
```

## Security Considerations

### Token Security

**Storage:**
- Tokens stored in localStorage (acceptable for this use case)
- Cleared on logout
- Never logged to console
- Never sent in URL parameters

**Transmission:**
- Always use HTTPS in production
- Tokens sent in Authorization header
- Never in query parameters or request body (except refresh)

### Password Security

**Frontend:**
- Never logged
- Cleared after submission
- Masked in input field
- Strength validation

**Backend:**
- Hashed by Supabase Auth
- Never stored in plain text
- Never returned in responses
- Minimum length enforced

### API Security

**Authentication:**
- All profile endpoints require valid JWT
- Tokens verified on every request
- Expired tokens rejected with 401
- Invalid tokens rejected with 401

**Authorization:**
- Users can only access their own data
- User ID extracted from JWT token
- Database queries scoped to user ID

**Rate Limiting:**
- Implemented on auth endpoints
- Prevents brute force attacks
- Configurable limits

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Quick Fixes

**"Network error" during registration:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend proxy configuration in `vite.config.ts`
3. Verify `VITE_API_URL` in `.env`

**"User already exists" error:**
1. Use a different email address
2. Or delete user from Supabase dashboard

**Tokens not persisting:**
1. Check browser localStorage in DevTools
2. Verify `setTokens()` is called after signup
3. Check for JavaScript errors in console

**401 errors on step 2:**
1. Verify token is in localStorage
2. Check Authorization header in Network tab
3. Verify token hasn't expired

## Performance Considerations

### Frontend Optimization

**Bundle Size:**
- Code-split authentication routes
- Lazy load onboarding components
- Tree-shake unused dependencies

**API Calls:**
- Debounce validation checks
- Cache user session data
- Prevent double-submission with loading states

### Backend Optimization

**Database Queries:**
- Indexed on user_id columns
- Connection pooling enabled
- Minimal joins

**Token Verification:**
- Cached public keys
- Connection pooling to Supabase
- Async/await throughout

**Target Response Times:**
- Auth endpoints: < 200ms
- Profile endpoints: < 500ms

## Deployment

### Environment Variables

**Frontend (.env):**
```bash
VITE_API_URL=/api  # Development
# VITE_API_URL=https://api.studymate.com/api  # Production
```

**Backend (.env):**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...
CORS_ORIGINS=http://localhost:5173,https://studymate.com
```

### Database Setup

Run migrations to create required tables:

```bash
cd python-backend
python scripts/run_migrations.py
```

### Monitoring

**Frontend:**
- Track signup success/failure rates
- Monitor API error rates
- Track page load times

**Backend:**
- Monitor endpoint response times
- Track authentication failures
- Monitor database connection pool
- Alert on high error rates

## Future Enhancements

### Planned Features

**Email Verification:**
- Send verification email on signup
- Require confirmation before full access
- Resend verification option

**Social Authentication:**
- Google OAuth
- GitHub OAuth
- Microsoft OAuth

**Multi-Factor Authentication:**
- TOTP support
- SMS verification
- Backup codes

**Password Reset:**
- Email-based reset flow
- Secure token generation
- Password update endpoint

**Profile Completion Tracking:**
- Progress indicator
- Skip optional steps
- Completion reminders

## Related Documentation

- [API Endpoints](../python-backend/API_ENDPOINTS.md) - Complete API reference
- [Environment Setup](./ENVIRONMENT_SETUP.md) - Environment configuration
- [Database Schema](./database-schema.md) - Database structure
- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Common issues and solutions
