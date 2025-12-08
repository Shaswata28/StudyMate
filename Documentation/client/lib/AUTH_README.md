# Authentication Implementation Guide

This document explains how the authentication system is implemented in the StudyMate frontend.

## Overview

The authentication system provides:
- User registration (signup) with academic profile
- User login
- Token-based authentication (JWT)
- Automatic token refresh
- User preference management
- Protected routes

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Components                      │
│  (Login, Signup, Questions, Dashboard, etc.)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ uses
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   useAuth() Hook                         │
│  - Manages auth state (user, isAuthenticated)           │
│  - Provides auth functions (login, signup, logout)      │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  AuthService Class                       │
│  - API communication                                     │
│  - Token management (localStorage)                      │
│  - Automatic token refresh                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP requests
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (/api/auth/*)               │
│  - /signup, /login, /logout, /session, /refresh         │
└─────────────────────────────────────────────────────────┘
```

## Files

### Core Files

1. **`client/lib/auth.ts`** - Authentication service
   - `AuthService` class with all auth methods
   - Token management
   - API communication
   - Singleton instance exported as `authService`

2. **`client/hooks/use-auth.ts`** - React hook for auth
   - Manages auth state in React components
   - Provides easy-to-use auth functions
   - Handles loading states

3. **`client/components/ProtectedRoute.tsx`** - Route protection
   - Wraps protected routes
   - Redirects to login if not authenticated
   - Shows loading state during auth check

### Updated Pages

4. **`client/pages/Login.tsx`** - Login page
   - Uses `useAuth()` hook
   - Calls `login()` function
   - Handles errors and success

5. **`client/pages/Signup.tsx`** - Registration page
   - Two-step signup process
   - Step 1: Email/password (creates user account)
   - Step 2: Academic profile (saves to database)

6. **`client/pages/Questions.tsx`** - Preference questionnaire
   - Converts answers to preference format
   - Saves to backend via `savePreferences()`
   - Navigates to dashboard on completion

## Usage Examples

### 1. Using the Auth Hook in Components

```typescript
import { useAuth } from '@/hooks/use-auth';

function MyComponent() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  return (
    <div>
      <p>Welcome, {user?.email}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### 2. Making Authenticated API Requests

```typescript
import { authService } from '@/lib/auth';

async function fetchUserCourses() {
  try {
    const response = await authService.fetchWithAuth('/api/courses');
    
    if (!response.ok) {
      throw new Error('Failed to fetch courses');
    }
    
    const courses = await response.json();
    return courses;
  } catch (error) {
    console.error('Error fetching courses:', error);
    throw error;
  }
}
```

### 3. Protecting Routes

In your `App.tsx` or router configuration:

```typescript
import { ProtectedRoute } from '@/components/ProtectedRoute';
import Dashboard from '@/pages/Dashboard';

<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/signup" element={<Signup />} />
  
  {/* Protected routes */}
  <Route
    path="/app"
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    }
  />
</Routes>
```

### 4. Login Flow

```typescript
import { useAuth } from '@/hooks/use-auth';
import { toast } from '@/lib/toast';

function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login({ email, password });
      toast.success('Login successful!');
      navigate('/app');
    } catch (error) {
      toast.error('Login failed', error.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
    </form>
  );
}
```

### 5. Signup Flow

```typescript
import { useAuth } from '@/hooks/use-auth';

function SignupPage() {
  const { signup, saveAcademicProfile } = useAuth();

  const handleSignup = async () => {
    try {
      // Step 1: Create account
      await signup({ email, password });
      
      // Step 2: Save academic profile
      await saveAcademicProfile({
        grade: ['Bachelor'],
        semester_type: 'double',
        semester: 3,
        subject: ['Computer Science']
      });
      
      navigate('/onboarding');
    } catch (error) {
      toast.error('Signup failed', error.message);
    }
  };
}
```

## Token Management

### Storage

Tokens are stored in `localStorage`:
- `studymate_access_token` - JWT access token (expires in ~1 hour)
- `studymate_refresh_token` - Refresh token (longer expiration)
- `studymate_user` - User information (JSON)

### Automatic Refresh

The `fetchWithAuth()` method automatically handles token refresh:

1. Makes API request with access token
2. If receives 401 Unauthorized:
   - Calls `/api/auth/refresh` with refresh token
   - Gets new access token
   - Retries original request
3. If refresh fails:
   - Clears tokens
   - Throws error (user needs to login again)

### Manual Token Check

```typescript
import { authService } from '@/lib/auth';

// Check if user is authenticated
if (authService.isAuthenticated()) {
  console.log('User is logged in');
}

// Get current user
const user = authService.getCurrentUser();
console.log('User:', user);

// Get session from backend
const session = await authService.getSession();
```

## API Endpoints Used

### Authentication Endpoints

- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/session` - Get current session
- `POST /api/auth/refresh` - Refresh access token

### Profile Endpoints

- `POST /api/academic` - Save academic profile
- `GET /api/academic` - Get academic profile
- `POST /api/preferences` - Save user preferences
- `GET /api/preferences` - Get user preferences

## Environment Variables

Create a `.env` file in the client directory:

```env
# API Base URL (optional, defaults to /api)
VITE_API_URL=http://localhost:8000/api
```

## Error Handling

All auth functions throw errors that can be caught:

```typescript
try {
  await login({ email, password });
} catch (error) {
  if (error instanceof Error) {
    // error.message contains the error description
    toast.error('Login failed', error.message);
  }
}
```

Common error messages:
- "Invalid email or password" - Wrong credentials
- "A user with this email already exists" - Duplicate signup
- "Authentication failed. Please login again." - Token expired and refresh failed
- "No access token available" - User not logged in

## Security Best Practices

1. **HTTPS Only**: Always use HTTPS in production
2. **Token Storage**: Tokens are in localStorage (consider httpOnly cookies for production)
3. **Token Expiration**: Access tokens expire after 1 hour
4. **Automatic Logout**: User is logged out if refresh token expires
5. **Protected Routes**: Use `<ProtectedRoute>` for authenticated pages

## Testing

### Manual Testing

1. **Signup Flow**:
   ```
   1. Go to /signup
   2. Fill in email/password (Step 1)
   3. Fill in academic info (Step 2)
   4. Should redirect to /onboarding
   5. Check localStorage for tokens
   ```

2. **Login Flow**:
   ```
   1. Go to /login
   2. Enter credentials
   3. Should redirect to /app
   4. Check localStorage for tokens
   ```

3. **Protected Route**:
   ```
   1. Clear localStorage
   2. Try to access /app
   3. Should redirect to /login
   ```

4. **Token Refresh**:
   ```
   1. Login
   2. Wait for token to expire (or manually expire it)
   3. Make an API request
   4. Should automatically refresh and succeed
   ```

### Debugging

Enable console logging in `auth.ts`:

```typescript
// Add at the top of methods
console.log('Auth: Login attempt', { email });
console.log('Auth: Token refresh');
console.log('Auth: Logout');
```

Check localStorage in browser DevTools:
```javascript
// In browser console
localStorage.getItem('studymate_access_token')
localStorage.getItem('studymate_refresh_token')
localStorage.getItem('studymate_user')
```

## Troubleshooting

### "No access token available"
- User is not logged in
- Tokens were cleared
- Solution: Redirect to login page

### "Authentication failed. Please login again."
- Refresh token expired
- Solution: User needs to login again

### CORS errors
- Backend not configured for frontend origin
- Solution: Add frontend URL to `ALLOWED_ORIGINS` in backend `.env`

### 401 Unauthorized on all requests
- Access token invalid or expired
- Refresh token not working
- Solution: Check backend logs, verify token format

## Next Steps

1. **Add Remember Me**: Implement persistent sessions
2. **Add Password Reset**: Forgot password flow
3. **Add Email Verification**: Verify email before full access
4. **Add Social Login**: Google, GitHub OAuth
5. **Add 2FA**: Two-factor authentication
6. **Move to httpOnly Cookies**: More secure token storage

## Support

For issues or questions:
1. Check backend logs in `python-backend/`
2. Check browser console for errors
3. Verify environment variables are set
4. Test API endpoints directly with cURL or Postman
