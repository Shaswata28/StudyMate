# Registration Flow Test Guide

This guide will help you test the complete registration flow connecting the frontend and backend.

## Prerequisites

1. **Backend Setup**: Python FastAPI backend must be running
2. **Frontend Setup**: Vite dev server must be running
3. **Database**: Supabase database must be configured and accessible

## Configuration Changes Made

### 1. Vite Proxy Configuration (`vite.config.ts`)
Updated the proxy configuration to forward ALL `/api` requests to the Python backend:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

This ensures that:
- `/api/auth/signup` → `http://localhost:8000/api/auth/signup`
- `/api/auth/login` → `http://localhost:8000/api/auth/login`
- `/api/academic` → `http://localhost:8000/api/academic`
- All other `/api/*` routes are proxied correctly

## Starting the Servers

### 1. Start the Python Backend

```bash
cd python-backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. Start the Frontend Dev Server

```bash
pnpm dev
```

You should see output like:
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:8080/
➜  Network: use --host to expose
```

## Testing the Registration Flow

### Step 1: Navigate to Signup Page

1. Open your browser to `http://localhost:8080/signup`
2. You should see the registration form with two steps

### Step 2: Complete Step 1 (Security)

Fill in the following fields:
- **Name**: Test User
- **Email**: test@example.com (use a unique email each time)
- **Password**: TestPassword123
- **Confirm Password**: TestPassword123
- **Terms**: Check the box

Click the arrow button to proceed to Step 2.

### Step 3: Complete Step 2 (Academic Profile)

Fill in the following fields:
- **Grade**: Bachelor (or any grade)
- **Semester Type**: Double or Tri
- **Semester**: Select a number (1-12)
- **Subject**: Select a subject (CS, EEE, English, BA, Economics)

Click the arrow button to complete registration.

### Expected Behavior

1. **Loading State**: The submit button should show a spinner
2. **Success**: You should see a success toast message
3. **Redirect**: After ~600ms, you should be redirected to `/onboarding`

### What Happens Behind the Scenes

1. **Frontend** (`client/pages/Signup.tsx`):
   - Validates form inputs
   - Calls `signup({ email, password })` from `useAuth` hook
   - Calls `saveAcademicProfile({ grade, semester_type, semester, subject })` from `useAuth` hook

2. **Auth Service** (`client/lib/auth.ts`):
   - `signup()` → POST `/api/auth/signup`
   - Stores access_token and refresh_token in localStorage
   - `saveAcademicProfile()` → POST `/api/academic` (with Bearer token)

3. **Backend** (`python-backend/routers/auth.py`):
   - `/api/auth/signup` → Creates user in Supabase Auth
   - Returns JWT tokens and user info

4. **Backend** (`python-backend/routers/academic.py`):
   - `/api/academic` → Verifies JWT token
   - Inserts academic profile into `academic` table
   - Links profile to user via user ID

## Troubleshooting

### Backend Not Responding

**Check if backend is running:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"studymate-ai-chat"}
```

**Check backend logs:**
Look for errors in the terminal where you started uvicorn.

### Frontend Can't Connect to Backend

**Check browser console:**
1. Open DevTools (F12)
2. Go to Network tab
3. Try to register
4. Look for failed requests to `/api/auth/signup` or `/api/academic`

**Common issues:**
- Backend not running on port 8000
- CORS errors (check `ALLOWED_ORIGINS` in `python-backend/.env`)
- Proxy not configured correctly in `vite.config.ts`

### Database Errors

**Check Supabase connection:**
```bash
cd python-backend
python test_connection.py
```

**Common issues:**
- Invalid Supabase credentials in `python-backend/.env`
- RLS policies blocking inserts
- Missing tables (`academic`, `personalized`, etc.)

### User Already Exists Error

If you see "A user with this email already exists":
- Use a different email address
- Or delete the user from Supabase dashboard (Authentication → Users)

## Verifying Registration Success

### 1. Check Supabase Dashboard

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Authentication** → **Users**
4. You should see the newly registered user

### 2. Check Academic Profile

1. In Supabase dashboard, go to **Table Editor**
2. Select the `academic` table
3. You should see a row with:
   - `id`: User's UUID
   - `grade`: Array of grades
   - `semester_type`: 'double' or 'tri'
   - `semester`: Number
   - `subject`: Array of subjects

### 3. Test Login

1. Navigate to `http://localhost:8080/login`
2. Enter the email and password you used during registration
3. You should be logged in successfully

## API Endpoints Reference

### Authentication Endpoints

- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login existing user
- `POST /api/auth/logout` - Logout current user
- `GET /api/auth/session` - Get current session
- `POST /api/auth/refresh` - Refresh access token

### Profile Endpoints

- `POST /api/academic` - Create academic profile
- `GET /api/academic` - Get academic profile
- `PUT /api/academic` - Update academic profile

## Testing with cURL

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123"}'
```

### 2. Save Academic Profile

```bash
# Replace YOUR_ACCESS_TOKEN with the token from signup response
curl -X POST http://localhost:8000/api/academic \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "grade": ["Bachelor"],
    "semester_type": "double",
    "semester": 1,
    "subject": ["computer science"]
  }'
```

## Success Criteria

✅ User can complete Step 1 (Security) without errors
✅ User can complete Step 2 (Academic Profile) without errors
✅ User is redirected to `/onboarding` after successful registration
✅ User appears in Supabase Auth dashboard
✅ Academic profile appears in `academic` table
✅ User can login with the registered credentials

## Next Steps

After successful registration testing:
1. Test the login flow
2. Test the onboarding questionnaire
3. Test the dashboard with authenticated user
4. Test logout functionality
5. Test token refresh mechanism
