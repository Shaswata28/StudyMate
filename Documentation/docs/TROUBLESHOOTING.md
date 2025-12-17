# Troubleshooting Guide - Registration Flow

This guide helps you diagnose and fix common issues with the registration flow.

## Table of Contents

- [Backend Connection Issues](#backend-connection-issues)
- [Authentication Errors](#authentication-errors)
- [Database Errors](#database-errors)
- [Frontend Issues](#frontend-issues)
- [Token Management Issues](#token-management-issues)
- [Validation Errors](#validation-errors)
- [Environment Configuration Issues](#environment-configuration-issues)

---

## Backend Connection Issues

### Issue: "Network error" or "Failed to fetch"

**Symptoms:**
- Registration fails immediately
- Browser console shows network error
- No request appears in Network tab

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"studymate-ai-chat"}
```

**Solutions:**

1. **Start the backend server:**
   ```bash
   cd python-backend
   source venv/bin/activate  # Windows: venv\Scripts\activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Check backend logs:**
   - Look for errors in the terminal where uvicorn is running
   - Check for port conflicts (another service using port 8000)

3. **Verify backend is accessible:**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/health
   
   # Test signup endpoint
   curl -X POST http://localhost:8000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123456"}'
   ```

---

### Issue: CORS errors in browser console

**Symptoms:**
- Error message: "Access to fetch at '...' from origin '...' has been blocked by CORS policy"
- Request shows as failed in Network tab
- Backend receives request but browser blocks response

**Diagnosis:**
Check browser console for exact CORS error message.

**Solutions:**

1. **Use same-origin configuration (recommended):**
   ```bash
   # .env
   VITE_API_URL=/api
   ```
   This uses relative URLs and avoids CORS issues.

2. **Configure CORS in backend:**
   Edit `python-backend/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:5173",
           "http://localhost:8080",
           # Add your frontend URL
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Restart both servers:**
   ```bash
   # Restart backend
   cd python-backend
   uvicorn main:app --reload
   
   # Restart frontend
   pnpm dev
   ```

---

### Issue: Proxy not working

**Symptoms:**
- Requests to `/api/*` return 404
- Backend is running but frontend can't reach it
- Using `VITE_API_URL=/api` but requests fail

**Diagnosis:**
Check `vite.config.ts` proxy configuration.

**Solutions:**

1. **Verify proxy configuration:**
   ```typescript
   // vite.config.ts
   export default defineConfig({
     server: {
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true,
         },
       },
     },
   });
   ```

2. **Restart Vite dev server:**
   ```bash
   # Stop the server (Ctrl+C)
   # Start again
   pnpm dev
   ```

3. **Use explicit URL instead:**
   ```bash
   # .env
   VITE_API_URL=http://localhost:8000/api
   ```

---

## Authentication Errors

### Issue: "A user with this email already exists"

**Symptoms:**
- Signup fails with 400 error
- Error message about duplicate email
- Can't register with the same email twice

**Solutions:**

1. **Use a different email address:**
   - Try a unique email for testing
   - Use email+tag format: `user+test1@example.com`

2. **Delete existing user from Supabase:**
   - Go to Supabase Dashboard
   - Navigate to Authentication → Users
   - Find and delete the user
   - Try registration again

3. **Login instead of signup:**
   - If you already have an account, use the login page
   - Navigate to `/login`

---

### Issue: "Invalid email or password"

**Symptoms:**
- Login fails with 401 error
- Credentials are correct but login doesn't work
- Just registered but can't login

**Solutions:**

1. **Verify credentials:**
   - Check for typos in email/password
   - Ensure caps lock is off
   - Try copying and pasting

2. **Check email confirmation:**
   - In development, emails should be auto-confirmed
   - Check Supabase dashboard: Authentication → Users
   - Verify `email_confirmed_at` is set

3. **Reset password:**
   - Use password reset flow (if implemented)
   - Or delete user and re-register

4. **Check backend logs:**
   ```bash
   # Look for authentication errors
   # Check Supabase connection
   ```

---

### Issue: "Invalid or expired authentication token"

**Symptoms:**
- Step 2 (academic profile) fails with 401
- Preferences submission fails with 401
- Token was working but now returns 401

**Diagnosis:**
```javascript
// Check token in browser console
console.log(localStorage.getItem('access_token'));

// Check token expiration
const token = localStorage.getItem('access_token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('Expires:', new Date(payload.exp * 1000));
```

**Solutions:**

1. **Token expired - refresh it:**
   ```javascript
   // Frontend should automatically refresh
   // Check if refresh token is present
   console.log(localStorage.getItem('refresh_token'));
   ```

2. **Token missing - re-login:**
   ```bash
   # Clear storage and login again
   localStorage.clear();
   # Navigate to /login
   ```

3. **Token malformed - clear and re-login:**
   ```javascript
   // Check token format
   const token = localStorage.getItem('access_token');
   console.log(token.split('.').length); // Should be 3
   ```

4. **Backend can't verify token:**
   - Check Supabase credentials in backend `.env`
   - Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Restart backend server

---

## Database Errors

### Issue: "Academic profile already exists"

**Symptoms:**
- Step 2 fails with 409 error
- Message: "Academic profile already exists. Use PUT to update."
- Can't create profile even though it's first time

**Solutions:**

1. **Update instead of create:**
   - Use PUT endpoint instead of POST
   - Or implement update logic in frontend

2. **Delete existing profile:**
   ```sql
   -- In Supabase SQL Editor
   DELETE FROM academic WHERE id = 'user-uuid-here';
   ```

3. **Check for orphaned data:**
   - User might have been deleted but profile remains
   - Clean up database manually

---

### Issue: Database connection errors

**Symptoms:**
- 500 errors on all endpoints
- Backend logs show Supabase connection errors
- "Could not connect to database"

**Diagnosis:**
```bash
cd python-backend
python test_connection.py
```

**Solutions:**

1. **Verify Supabase credentials:**
   ```bash
   # Check python-backend/.env
   cat python-backend/.env
   
   # Verify these are set:
   # SUPABASE_URL=https://xxx.supabase.co
   # SUPABASE_ANON_KEY=eyJxxx...
   # SUPABASE_SERVICE_KEY=eyJxxx...
   ```

2. **Get correct credentials:**
   - Go to Supabase Dashboard
   - Navigate to Settings → API
   - Copy URL and keys
   - Update `.env` file

3. **Check network connectivity:**
   ```bash
   # Test connection to Supabase
   curl https://your-project.supabase.co
   ```

4. **Verify tables exist:**
   - Go to Supabase Dashboard
   - Navigate to Table Editor
   - Verify `academic` and `personalized` tables exist
   - Run migrations if needed:
     ```bash
     cd python-backend
     python scripts/run_migrations.py
     ```

---

### Issue: Row Level Security (RLS) blocking inserts

**Symptoms:**
- 500 errors when creating profiles
- Backend logs show permission denied
- "new row violates row-level security policy"

**Solutions:**

1. **Disable RLS for testing:**
   ```sql
   -- In Supabase SQL Editor
   ALTER TABLE academic DISABLE ROW LEVEL SECURITY;
   ALTER TABLE personalized DISABLE ROW LEVEL SECURITY;
   ```

2. **Configure RLS policies correctly:**
   ```sql
   -- Allow users to insert their own data
   CREATE POLICY "Users can insert own academic profile"
   ON academic FOR INSERT
   WITH CHECK (auth.uid() = id);
   
   CREATE POLICY "Users can insert own preferences"
   ON personalized FOR INSERT
   WITH CHECK (auth.uid() = id);
   ```

3. **Use service key for admin operations:**
   - Backend should use `SUPABASE_SERVICE_KEY` for admin operations
   - Check `python-backend/services/supabase_client.py`

---

## Frontend Issues

### Issue: Form validation not working

**Symptoms:**
- Can submit form with invalid data
- No error messages shown
- Validation errors not displayed

**Solutions:**

1. **Check validation logic:**
   ```typescript
   // client/pages/Signup.tsx
   const validateStep1 = () => {
     const errors: any = {};
     
     if (!email) errors.email = "Email is required";
     if (!password || password.length < 8) {
       errors.password = "Password must be at least 8 characters";
     }
     // ... more validation
     
     return errors;
   };
   ```

2. **Verify error state:**
   ```typescript
   // Check if errors are being set
   console.log('Validation errors:', step1Errors);
   ```

3. **Check error display:**
   ```typescript
   // Ensure errors are rendered
   {step1Errors.email && (
     <p className="text-red-500">{step1Errors.email}</p>
   )}
   ```

---

### Issue: Not redirecting after successful registration

**Symptoms:**
- Registration succeeds but stays on signup page
- No navigation to onboarding
- Tokens are stored but no redirect

**Solutions:**

1. **Check navigation logic:**
   ```typescript
   // client/pages/Signup.tsx
   const handleStep2Submit = async () => {
     try {
       await saveAcademicProfile(profileData);
       
       // Should navigate here
       navigate('/onboarding');
     } catch (error) {
       // Handle error
     }
   };
   ```

2. **Verify React Router setup:**
   ```typescript
   // client/App.tsx
   <Route path="/onboarding" element={<Onboarding />} />
   ```

3. **Check for JavaScript errors:**
   - Open browser console
   - Look for errors preventing navigation
   - Fix any errors found

---

### Issue: Loading state stuck

**Symptoms:**
- Submit button shows spinner indefinitely
- Form appears to be submitting but never completes
- Can't interact with form

**Solutions:**

1. **Check loading state management:**
   ```typescript
   const [isLoading, setIsLoading] = useState(false);
   
   const handleSubmit = async () => {
     setIsLoading(true);
     try {
       await signup(data);
     } catch (error) {
       // Handle error
     } finally {
       setIsLoading(false); // Always reset loading state
     }
   };
   ```

2. **Check for unhandled errors:**
   - Errors might prevent loading state from resetting
   - Add proper error handling
   - Use finally block to reset state

3. **Reload page:**
   - Refresh browser to reset state
   - Check console for errors

---

## Token Management Issues

### Issue: Tokens not persisting

**Symptoms:**
- Tokens disappear after page refresh
- User logged out unexpectedly
- localStorage appears empty

**Diagnosis:**
```javascript
// Check localStorage in browser console
console.log('Access token:', localStorage.getItem('access_token'));
console.log('Refresh token:', localStorage.getItem('refresh_token'));
console.log('User:', localStorage.getItem('user'));
```

**Solutions:**

1. **Verify token storage:**
   ```typescript
   // client/lib/auth.ts
   private setTokens(authData: AuthResponse) {
     localStorage.setItem('access_token', authData.access_token);
     localStorage.setItem('refresh_token', authData.refresh_token);
     localStorage.setItem('user', JSON.stringify(authData.user));
   }
   ```

2. **Check if setTokens is called:**
   ```typescript
   const signup = async (data: SignupData) => {
     const response = await fetch(`${API_BASE_URL}/auth/signup`, {
       method: 'POST',
       body: JSON.stringify(data)
     });
     
     const authData = await response.json();
     this.setTokens(authData); // Make sure this is called
     return authData;
   };
   ```

3. **Check browser settings:**
   - Ensure localStorage is enabled
   - Check if in private/incognito mode
   - Try different browser

---

### Issue: Token refresh not working

**Symptoms:**
- 401 errors after token expires
- User logged out when token expires
- Refresh endpoint returns error

**Diagnosis:**
```bash
# Test refresh endpoint
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"your-refresh-token-here"}'
```

**Solutions:**

1. **Verify refresh logic:**
   ```typescript
   // client/lib/auth.ts
   private async fetchWithAuth(url: string, options: RequestInit) {
     let response = await fetch(url, {
       ...options,
       headers: {
         ...options.headers,
         'Authorization': `Bearer ${this.getAccessToken()}`
       }
     });
     
     if (response.status === 401) {
       // Attempt refresh
       await this.refreshToken();
       // Retry request
       response = await fetch(url, options);
     }
     
     return response;
   }
   ```

2. **Check refresh token validity:**
   - Refresh tokens expire after 7 days (default)
   - If expired, user must re-login
   - Check token expiration in Supabase dashboard

3. **Verify refresh endpoint:**
   - Test endpoint manually with curl
   - Check backend logs for errors
   - Verify Supabase configuration

---

## Validation Errors

### Issue: "Password must be at least 8 characters"

**Symptoms:**
- Can't submit signup form
- Password validation fails
- Error shown below password field

**Solutions:**

1. **Use longer password:**
   - Minimum 8 characters required
   - Use combination of letters, numbers, symbols
   - Example: `SecurePass123`

2. **Check password field:**
   - Ensure no extra spaces
   - Check if copying from password manager
   - Type password manually

---

### Issue: "Grade is required" or other field validation errors

**Symptoms:**
- Step 2 validation fails
- Required field errors shown
- Can't proceed to onboarding

**Solutions:**

1. **Fill all required fields:**
   - Grade: Select at least one
   - Semester Type: Select double or tri
   - Semester: Select a number
   - Subject: Select at least one

2. **Check field values:**
   ```typescript
   console.log('Form data:', {
     grade,
     semester_type,
     semester,
     subject
   });
   ```

3. **Verify validation logic:**
   ```typescript
   const validateStep2 = () => {
     const errors: any = {};
     
     if (!grade || grade.length === 0) {
       errors.grade = "Grade is required";
     }
     // ... more validation
     
     return errors;
   };
   ```

---

## Environment Configuration Issues

### Issue: API requests going to wrong URL

**Symptoms:**
- Requests go to wrong domain
- 404 errors on API calls
- Network tab shows unexpected URLs

**Diagnosis:**
```javascript
// Check configured API URL
console.log('API Base URL:', import.meta.env.VITE_API_URL);
```

**Solutions:**

1. **Verify .env file:**
   ```bash
   # Check .env in project root
   cat .env
   
   # Should contain:
   VITE_API_URL=/api
   ```

2. **Restart dev server:**
   ```bash
   # Stop server (Ctrl+C)
   # Start again
   pnpm dev
   ```
   Environment variables are read at startup.

3. **Check for typos:**
   - Variable must start with `VITE_`
   - Check spelling: `VITE_API_URL`
   - No extra spaces or quotes

4. **Verify usage in code:**
   ```typescript
   // client/lib/constants.ts
   export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
   
   // client/lib/auth.ts
   import { API_BASE_URL } from './constants';
   fetch(`${API_BASE_URL}/auth/signup`, ...);
   ```

---

### Issue: Environment variables not loading

**Symptoms:**
- `import.meta.env.VITE_API_URL` is undefined
- API calls fail with undefined URL
- Console shows "undefined/auth/signup"

**Solutions:**

1. **Check .env file location:**
   - Must be in project root (same level as package.json)
   - Not in subdirectories

2. **Check variable name:**
   - Must start with `VITE_` prefix
   - Vite only exposes variables with this prefix

3. **Restart dev server:**
   - Changes to .env require restart
   - Stop and start `pnpm dev`

4. **Use fallback value:**
   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
   ```

---

## General Debugging Tips

### Enable Verbose Logging

**Frontend:**
```typescript
// Add console logs to track flow
console.log('Starting signup...');
console.log('Form data:', formData);
console.log('Response:', response);
```

**Backend:**
```python
# Check backend logs
# Uvicorn shows all requests and errors
# Look for stack traces
```

### Use Browser DevTools

1. **Network Tab:**
   - See all API requests
   - Check request/response headers
   - View request/response bodies
   - Check status codes

2. **Console Tab:**
   - See JavaScript errors
   - View console.log output
   - Check for warnings

3. **Application Tab:**
   - View localStorage
   - Check stored tokens
   - Clear storage if needed

### Test with cURL

```bash
# Test signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123456"}'

# Test academic profile (replace TOKEN)
curl -X POST http://localhost:8000/api/academic \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"grade":["Bachelor"],"semester_type":"double","semester":1,"subject":["CS"]}'
```

### Check Server Health

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost:5173
```

---

## Getting Help

If you're still experiencing issues:

1. **Check existing documentation:**
   - [Registration Flow](./REGISTRATION_FLOW.md)
   - [API Reference](./API_REFERENCE.md)
   - [Environment Setup](./ENVIRONMENT_SETUP.md)

2. **Gather information:**
   - Error messages (exact text)
   - Browser console output
   - Backend logs
   - Steps to reproduce

3. **Create a minimal reproduction:**
   - Isolate the issue
   - Test with minimal code
   - Document steps

4. **Check for known issues:**
   - Review GitHub issues
   - Search error messages
   - Check Supabase status

---

## Quick Reference

### Common Commands

```bash
# Start backend
cd python-backend
source venv/bin/activate
uvicorn main:app --reload

# Start frontend
pnpm dev

# Test backend health
curl http://localhost:8000/health

# Test connection
cd python-backend
python test_connection.py

# Run tests
pnpm test
cd python-backend && python test_auth_endpoints.py
```

### Common Fixes

```bash
# Clear localStorage
localStorage.clear()

# Restart servers
# Ctrl+C to stop, then restart

# Clear browser cache
# Ctrl+Shift+Delete

# Reinstall dependencies
pnpm install
cd python-backend && pip install -r requirements.txt
```

### Environment Variables

```bash
# Frontend (.env)
VITE_API_URL=/api

# Backend (python-backend/.env)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...
```
