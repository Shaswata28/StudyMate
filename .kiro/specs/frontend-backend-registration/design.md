# Design Document: Frontend-Backend Registration Integration

## Overview

This design document outlines the integration between the React frontend and Python FastAPI backend for user registration. The system implements a three-step registration flow:

1. **Security Step**: User provides email and password credentials
2. **Academic Profile Step**: User provides educational information (grade, semester, subjects)
3. **Preferences Step**: User sets learning preferences through the onboarding questionnaire

The integration uses JWT-based authentication with Supabase as the authentication provider. The frontend manages tokens in localStorage and automatically handles token refresh for expired access tokens. All API communication follows RESTful conventions with proper error handling and user feedback.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Signup.tsx   │  │ Onboarding   │  │ use-auth.ts  │      │
│  │ (Step 1 & 2) │  │ (Step 3)     │  │ (Hook)       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │   auth.ts       │                        │
│                   │ (Auth Service)  │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │ HTTP/JSON
                             │ JWT Bearer Token
┌────────────────────────────▼─────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ auth.py      │  │ academic.py  │  │preferences.py│      │
│  │ (Router)     │  │ (Router)     │  │ (Router)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ auth_service.py │                        │
│                   │ (JWT Verify)    │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ supabase_client │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    Supabase     │
                    │  Auth + Database│
                    └─────────────────┘
```

### Component Interaction Flow

**Registration Flow:**

1. User fills Step 1 (email/password) → Frontend validates → POST `/api/auth/signup`
2. Backend creates user in Supabase Auth → Returns JWT tokens + user info
3. Frontend stores tokens in localStorage → Shows Step 2
4. User fills Step 2 (academic info) → Frontend validates → POST `/api/academic` (with JWT)
5. Backend verifies JWT → Creates academic profile in database
6. Frontend navigates to onboarding → User fills preferences
7. User submits preferences → POST `/api/preferences` (with JWT)
8. Backend verifies JWT → Creates preferences in database
9. Frontend navigates to dashboard

## Components and Interfaces

### Frontend Components

#### 1. Signup Component (`client/pages/Signup.tsx`)

**Responsibilities:**
- Render two-step registration form
- Validate user input on both steps
- Manage form state and step transitions
- Call auth service for signup and academic profile
- Display error messages via toast notifications
- Navigate to onboarding on success

**Key State:**
```typescript
- step: SignupStep (1 | 2)
- name, email, password, confirmPassword: string
- grade, semesterType, semester, subject: string
- step1Errors, step2Errors: validation error objects
- isLoading: boolean
```

**Key Methods:**
- `validateStep1()`: Validates email, password, name, terms
- `validateStep2()`: Validates grade, semester type, semester, subject
- `handleStep1Submit()`: Calls signup, transitions to step 2
- `handleStep2Submit()`: Calls saveAcademicProfile, navigates to onboarding

#### 2. Auth Hook (`client/hooks/use-auth.ts`)

**Responsibilities:**
- Provide authentication state to components
- Expose auth functions (signup, login, logout)
- Manage loading states
- Initialize auth state on mount

**Interface:**
```typescript
interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signup: (data: SignupData) => Promise<AuthResponse>;
  login: (data: LoginData) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  saveAcademicProfile: (profile: AcademicProfile) => Promise<void>;
  savePreferences: (prefs: UserPreferences) => Promise<void>;
  getPreferences: () => Promise<UserPreferences | null>;
  getAcademicProfile: () => Promise<AcademicProfile | null>;
}
```

#### 3. Auth Service (`client/lib/auth.ts`)

**Responsibilities:**
- Handle all HTTP communication with backend
- Manage JWT tokens in localStorage
- Implement automatic token refresh
- Provide authenticated fetch wrapper

**Key Methods:**
- `signup(data)`: POST to `/api/auth/signup`
- `login(data)`: POST to `/api/auth/login`
- `logout()`: POST to `/api/auth/logout`, clear tokens
- `getSession()`: GET `/api/auth/session`, verify token validity
- `refreshToken()`: POST to `/api/auth/refresh`, get new access token
- `fetchWithAuth(url, options)`: Wrapper for authenticated requests
- `saveAcademicProfile(profile)`: POST to `/api/academic`
- `savePreferences(prefs)`: POST to `/api/preferences`

**Token Management:**
```typescript
- setTokens(authData): Store access_token, refresh_token, user in localStorage
- clearTokens(): Remove all auth data from localStorage
- getAccessToken(): Retrieve access token
- getRefreshToken(): Retrieve refresh token
- getCurrentUser(): Parse and return user object
```

### Backend Components

#### 1. Auth Router (`python-backend/routers/auth.py`)

**Endpoints:**

**POST `/api/auth/signup`**
- Request: `{ email: string, password: string }`
- Response: `AuthResponse` (201 Created)
- Errors: 400 (user exists), 500 (server error)
- Logic: Create user via Supabase Auth, return tokens

**POST `/api/auth/login`**
- Request: `{ email: string, password: string }`
- Response: `AuthResponse` (200 OK)
- Errors: 401 (invalid credentials), 500 (server error)
- Logic: Authenticate via Supabase, return tokens

**POST `/api/auth/logout`**
- Headers: `Authorization: Bearer <token>`
- Response: `{ message: string }` (200 OK)
- Errors: 401 (not authenticated), 500 (server error)
- Logic: Invalidate session via Supabase

**GET `/api/auth/session`**
- Headers: `Authorization: Bearer <token>`
- Response: `SessionResponse` (200 OK)
- Errors: 401 (invalid/expired), 500 (server error)
- Logic: Verify token, return user info

**POST `/api/auth/refresh`**
- Request: `{ refresh_token: string }`
- Response: `AuthResponse` (200 OK)
- Errors: 401 (invalid refresh token), 500 (server error)
- Logic: Exchange refresh token for new access token

#### 2. Academic Router (`python-backend/routers/academic.py`)

**Endpoints:**

**POST `/api/academic`**
- Headers: `Authorization: Bearer <token>`
- Request: `AcademicProfile`
- Response: Academic profile object (201 Created)
- Errors: 401 (not authenticated), 409 (already exists), 500 (server error)
- Logic: Verify JWT, create academic record in database

**GET `/api/academic`**
- Headers: `Authorization: Bearer <token>`
- Response: Academic profile object (200 OK)
- Errors: 401 (not authenticated), 404 (not found), 500 (server error)
- Logic: Verify JWT, retrieve academic record

**PUT `/api/academic`**
- Headers: `Authorization: Bearer <token>`
- Request: `AcademicProfile`
- Response: Updated academic profile (200 OK)
- Errors: 401 (not authenticated), 404 (not found), 500 (server error)
- Logic: Verify JWT, update academic record

#### 3. Preferences Router (`python-backend/routers/preferences.py`)

**Endpoints:**

**POST `/api/preferences`**
- Headers: `Authorization: Bearer <token>`
- Request: `UserPreferences`
- Response: Preferences object (201 Created)
- Errors: 401 (not authenticated), 409 (already exists), 500 (server error)
- Logic: Verify JWT, create preferences record as JSONB

**GET `/api/preferences`**
- Headers: `Authorization: Bearer <token>`
- Response: Preferences object (200 OK)
- Errors: 401 (not authenticated), 404 (not found), 500 (server error)
- Logic: Verify JWT, retrieve preferences record

**PUT `/api/preferences`**
- Headers: `Authorization: Bearer <token>`
- Request: `UserPreferences`
- Response: Updated preferences (200 OK)
- Errors: 401 (not authenticated), 404 (not found), 500 (server error)
- Logic: Verify JWT, update preferences record

#### 4. Auth Service (`python-backend/services/auth_service.py`)

**Responsibilities:**
- Verify JWT tokens using Supabase
- Extract user information from tokens
- Provide FastAPI dependencies for protected routes

**Key Functions:**
- `verify_jwt_token(token)`: Validate token with Supabase, return user data
- `get_user_from_token(token)`: Extract AuthUser object from token
- `get_current_user(credentials)`: FastAPI dependency for protected routes
- `get_current_user_optional(credentials)`: Optional auth dependency

**AuthUser Class:**
```python
class AuthUser:
    id: str          # User UUID
    email: str       # User email
    access_token: str # JWT for authenticated requests
```

## Data Models

### Frontend Types

```typescript
interface User {
  id: string;
  email: string;
  created_at: string;
  email_confirmed_at: string | null;
  last_sign_in_at?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: User;
}

interface SignupData {
  email: string;
  password: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface AcademicProfile {
  grade: string[];
  semester_type: 'double' | 'tri';
  semester: number;
  subject: string[];
}

interface UserPreferences {
  detail_level: number;        // 0-1 scale
  example_preference: number;  // 0-1 scale
  analogy_preference: number;  // 0-1 scale
  technical_language: number;  // 0-1 scale
  structure_preference: number; // 0-1 scale
  visual_preference: number;   // 0-1 scale
  learning_pace: 'slow' | 'moderate' | 'fast';
  prior_experience: 'beginner' | 'intermediate' | 'advanced' | 'expert';
}
```

### Backend Schemas

```python
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    user: dict

class AcademicProfile(BaseModel):
    grade: List[str]
    semester_type: Literal['double', 'tri']
    semester: int
    subject: List[str]

class UserPreferences(BaseModel):
    detail_level: float
    example_preference: float
    analogy_preference: float
    technical_language: float
    structure_preference: float
    visual_preference: float
    learning_pace: Literal['slow', 'moderate', 'fast']
    prior_experience: Literal['beginner', 'intermediate', 'advanced', 'expert']
```

### Database Schema

**auth.users** (Managed by Supabase Auth)
- `id`: UUID (primary key)
- `email`: string (unique)
- `encrypted_password`: string
- `created_at`: timestamp
- `email_confirmed_at`: timestamp (nullable)
- `last_sign_in_at`: timestamp (nullable)

**public.academic**
- `id`: UUID (primary key, foreign key to auth.users)
- `grade`: text[] (array of grade levels)
- `semester_type`: text ('double' or 'tri')
- `semester`: integer
- `subject`: text[] (array of subjects)
- `created_at`: timestamp
- `updated_at`: timestamp

**public.personalized**
- `id`: UUID (primary key, foreign key to auth.users)
- `prefs`: JSONB (flexible preferences object)
- `created_at`: timestamp
- `updated_at`: timestamp

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

Before defining the final properties, let's identify and eliminate redundancy:

**Redundancies Identified:**
1. Properties 1.4 and 1.5 (frontend token storage and error display) are covered by testing the auth service methods directly
2. Properties 2.2 and 9.2 (auth header inclusion) can be combined into a single property about all authenticated requests
3. Properties 3.1, 2.2, and 9.2 all test the same thing - auth header format - can be consolidated
4. Properties 6.2 and 6.3 (201 status codes) can be combined into one property about all creation endpoints
5. Properties 4.1, 4.2, and 6.4 overlap in testing error response formats - can be consolidated
6. Multiple edge cases (7.2, 7.3, 7.4, 8.1-8.4) test validation - these are better handled by unit tests than properties

**Consolidated Properties:**
- Combine all auth header properties into one comprehensive property
- Combine all HTTP status code properties into one property
- Combine all error handling properties into one property
- Focus properties on core behaviors rather than specific validation cases

### Core Correctness Properties

Property 1: Signup creates authenticated session
*For any* valid email and password combination, when signup is called, the backend should return an access token, refresh token, and user object, and the frontend should store these in localStorage
**Validates: Requirements 1.1, 1.2, 1.4**

Property 2: Duplicate email rejection
*For any* email that already exists in the system, attempting to signup with that email should result in a 400 error with message "A user with this email already exists"
**Validates: Requirements 1.3**

Property 3: Authenticated requests include bearer token
*For any* authenticated API request (academic profile, preferences, session), the request should include an Authorization header in the format "Bearer {access_token}"
**Validates: Requirements 2.2, 3.1, 9.2**

Property 4: Academic profile creation requires authentication
*For any* academic profile data, attempting to create it without a valid access token should result in a 401 error
**Validates: Requirements 2.4, 5.5**

Property 5: Valid academic profile creates database record
*For any* valid academic profile data with valid authentication, the backend should create a record in the academic table linked to the authenticated user's ID
**Validates: Requirements 2.3**

Property 6: Token refresh on 401 error
*For any* authenticated request that returns a 401 error, the frontend should attempt to refresh the access token using the refresh token, and if successful, retry the original request with the new token
**Validates: Requirements 3.2, 3.3, 3.4**

Property 7: Failed signup prevents step progression
*For any* signup attempt that fails, the frontend should remain on step 1 and not transition to step 2
**Validates: Requirements 5.1**

Property 8: Failed academic profile preserves authentication
*For any* academic profile submission that fails, the frontend should keep the user authenticated (tokens remain in localStorage)
**Validates: Requirements 5.2**

Property 9: HTTP status codes match operation types
*For any* successful creation operation (signup, academic profile, preferences), the backend should return 201; for validation errors, 400; for authentication errors, 401; for server errors, 500
**Validates: Requirements 6.2, 6.3, 6.4, 4.1, 4.2, 4.3**

Property 10: Error messages extracted from detail field
*For any* error response from the backend, the frontend should extract the error message from the response's "detail" field and display it via toast notification
**Validates: Requirements 4.4, 4.5, 1.5**

Property 11: Preferences creation requires authentication
*For any* preferences data, attempting to create it without a valid access token should result in a 401 error
**Validates: Requirements 9.4**

Property 12: Valid preferences creates database record
*For any* valid preferences data with valid authentication, the backend should create or update a record in the personalized table with the preferences stored as JSONB
**Validates: Requirements 9.3**

Property 13: API requests use configured base URL
*For any* API request made by the frontend, the URL should be constructed using the API_BASE_URL from environment variables
**Validates: Requirements 6.5**

Property 14: Content-Type header for JSON requests
*For any* POST request with a JSON body (signup, login, academic profile, preferences), the request should include Content-Type header set to "application/json"
**Validates: Requirements 6.1**

## Error Handling

### Frontend Error Handling

**Validation Errors:**
- Validate all form inputs before submission
- Display field-specific error messages below each input
- Prevent form submission if validation fails
- Clear error messages when user corrects input

**API Errors:**
- Extract error message from response `detail` field
- Display error via toast notification system
- Maintain form state on error (don't clear inputs)
- Log errors to console for debugging

**Network Errors:**
- Catch fetch exceptions
- Display generic "Network error" message
- Suggest user check connection
- Don't clear authentication state on network errors

**Token Expiration:**
- Automatically attempt token refresh on 401
- Retry original request with new token
- Only logout if refresh fails
- Transparent to user when successful

### Backend Error Handling

**Validation Errors (400):**
- Validate request body against Pydantic schemas
- Return descriptive error messages
- Include field names in error details when applicable
- Log validation failures for monitoring

**Authentication Errors (401):**
- Verify JWT token on all protected routes
- Return consistent error message: "Invalid or expired authentication token"
- Include WWW-Authenticate header
- Log authentication failures

**Conflict Errors (409):**
- Check for existing records before creation
- Return specific message: "Resource already exists. Use PUT to update."
- Suggest correct action to client
- Log conflict attempts

**Server Errors (500):**
- Catch all unexpected exceptions
- Return generic message: "An unexpected error occurred"
- Log full error details server-side
- Don't expose internal details to client

**Supabase Errors:**
- Wrap all Supabase calls in try-catch
- Map Supabase errors to appropriate HTTP status codes
- Log Supabase-specific errors for debugging
- Return user-friendly messages

## Testing Strategy

### Unit Testing

**Frontend Unit Tests:**
- Test validation functions (validateStep1, validateStep2)
- Test token management methods (setTokens, clearTokens, getAccessToken)
- Test error message extraction
- Test form state management
- Test navigation logic

**Backend Unit Tests:**
- Test JWT token verification
- Test AuthUser extraction from tokens
- Test Pydantic schema validation
- Test error response formatting
- Test database query construction

### Property-Based Testing

The system will use property-based testing to verify correctness properties across many randomly generated inputs:

**Frontend Property Tests (using fast-check):**
- Generate random valid/invalid emails and passwords
- Generate random academic profiles
- Generate random preferences
- Generate random API responses
- Verify properties hold across all generated inputs

**Backend Property Tests (using Hypothesis):**
- Generate random valid/invalid request bodies
- Generate random JWT tokens (valid/expired/malformed)
- Generate random user IDs
- Generate random database states
- Verify properties hold across all generated inputs

**Property Test Configuration:**
- Minimum 100 iterations per property test
- Use shrinking to find minimal failing examples
- Tag each test with property number from design doc
- Run property tests in CI/CD pipeline

### Integration Testing

**End-to-End Registration Flow:**
1. Submit step 1 with valid credentials
2. Verify tokens stored in localStorage
3. Submit step 2 with valid academic profile
4. Verify academic record created in database
5. Navigate to onboarding
6. Submit preferences
7. Verify preferences record created in database
8. Verify navigation to dashboard

**Token Refresh Flow:**
1. Create user and get tokens
2. Wait for access token to expire (or mock expiration)
3. Make authenticated request
4. Verify 401 response triggers refresh
5. Verify original request retried with new token
6. Verify request succeeds

**Error Handling Flow:**
1. Test duplicate email signup
2. Test invalid credentials login
3. Test missing required fields
4. Test expired tokens
5. Test network failures
6. Verify appropriate error messages displayed

### Manual Testing Checklist

- [ ] Complete registration flow with valid data
- [ ] Test with invalid email formats
- [ ] Test with weak passwords
- [ ] Test with mismatched passwords
- [ ] Test with missing required fields
- [ ] Test duplicate email registration
- [ ] Test browser refresh during registration
- [ ] Test back button navigation
- [ ] Test with network disconnected
- [ ] Test token expiration and refresh
- [ ] Verify data persists in database
- [ ] Verify error messages are user-friendly
- [ ] Test on different browsers
- [ ] Test responsive design on mobile

## Security Considerations

### Frontend Security

**Token Storage:**
- Store tokens in localStorage (acceptable for this use case)
- Clear tokens on logout
- Don't expose tokens in console logs
- Don't send tokens in URL parameters

**Password Handling:**
- Never log passwords
- Clear password fields after submission
- Use password input type to mask characters
- Validate password strength client-side

**XSS Prevention:**
- React automatically escapes rendered content
- Don't use dangerouslySetInnerHTML with user input
- Sanitize any HTML content before rendering

### Backend Security

**JWT Verification:**
- Verify all tokens using Supabase Auth
- Check token expiration
- Validate token signature
- Don't trust client-provided user IDs

**Password Security:**
- Delegate password hashing to Supabase Auth
- Enforce minimum password length (8 characters)
- Never log passwords
- Use HTTPS for all authentication requests

**SQL Injection Prevention:**
- Use Supabase client's parameterized queries
- Never construct SQL strings with user input
- Validate all input against Pydantic schemas

**Rate Limiting:**
- Implement rate limiting on auth endpoints
- Prevent brute force attacks
- Log suspicious activity
- Consider CAPTCHA for repeated failures

**CORS Configuration:**
- Configure allowed origins
- Don't use wildcard (*) in production
- Validate Origin header
- Set appropriate CORS headers

## Performance Considerations

### Frontend Performance

**Bundle Size:**
- Code-split authentication routes
- Lazy load onboarding components
- Minimize dependencies
- Use tree-shaking

**API Calls:**
- Debounce validation checks
- Cache user session data
- Minimize redundant requests
- Use loading states to prevent double-submission

**LocalStorage:**
- Minimize data stored
- Compress large objects if needed
- Clean up old data
- Handle storage quota errors

### Backend Performance

**Database Queries:**
- Use indexes on user_id columns
- Minimize joins
- Use connection pooling
- Cache frequently accessed data

**Token Verification:**
- Cache public keys for JWT verification
- Minimize calls to Supabase Auth
- Use connection pooling
- Consider token caching with short TTL

**Response Times:**
- Target < 200ms for auth endpoints
- Target < 500ms for profile endpoints
- Use async/await throughout
- Monitor slow queries

## Deployment Considerations

### Environment Variables

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000/api  # Development
VITE_API_URL=https://api.studymate.com/api  # Production
```

**Backend (.env):**
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...
CORS_ORIGINS=http://localhost:5173,https://studymate.com
```

### Database Migrations

**Required Tables:**
- `auth.users` (managed by Supabase)
- `public.academic` (create via migration)
- `public.personalized` (create via migration)

**Migration Scripts:**
- Create tables with proper foreign keys
- Add indexes on user_id columns
- Set up Row Level Security (RLS) policies
- Create triggers for updated_at timestamps

### Monitoring and Logging

**Frontend Monitoring:**
- Track signup success/failure rates
- Monitor API error rates
- Track page load times
- Log authentication errors

**Backend Monitoring:**
- Track endpoint response times
- Monitor error rates by endpoint
- Track authentication failures
- Monitor database connection pool
- Alert on high error rates

### Rollback Plan

**If Issues Arise:**
1. Revert frontend deployment
2. Revert backend deployment
3. Check database for partial registrations
4. Verify no data corruption
5. Communicate with affected users
6. Fix issues in development
7. Re-deploy with fixes

## Future Enhancements

### Potential Improvements

**Email Verification:**
- Send verification email on signup
- Require email confirmation before full access
- Resend verification email option
- Handle verification link clicks

**Social Authentication:**
- Add Google OAuth
- Add GitHub OAuth
- Add Microsoft OAuth
- Merge social and email accounts

**Multi-Factor Authentication:**
- Add TOTP support
- Add SMS verification
- Add backup codes
- Remember trusted devices

**Password Reset:**
- Send password reset email
- Validate reset tokens
- Update password securely
- Notify user of password change

**Profile Completion Tracking:**
- Track which steps completed
- Show progress indicator
- Allow skipping optional steps
- Remind users to complete profile

**Analytics:**
- Track registration funnel
- Identify drop-off points
- A/B test form variations
- Optimize conversion rates
