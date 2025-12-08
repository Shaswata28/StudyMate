# Environment Variable Setup Guide

## Overview

This guide explains how to configure environment variables for the StudyMate application, specifically focusing on the frontend API configuration.

## Frontend Environment Variables

### VITE_API_URL

The `VITE_API_URL` environment variable controls where the frontend sends API requests.

**Location:** `.env` file in the project root

**Format:**
```bash
VITE_API_URL=<base_url>
```

### Configuration Scenarios

#### 1. Development - Same Origin (Recommended)

**Use Case:** Running frontend and backend together, or using a proxy

**Configuration:**
```bash
VITE_API_URL=/api
```

**Advantages:**
- No CORS issues
- Simplest setup
- Works with Vite proxy
- Recommended for most developers

**How it works:**
- Frontend makes requests to `/api/auth/signup`, `/api/academic`, etc.
- Requests are relative to the current origin
- Works seamlessly with proxy or same-domain deployment

#### 2. Development - Different Ports

**Use Case:** Running frontend and backend on different ports without proxy

**Configuration:**
```bash
VITE_API_URL=http://localhost:8000/api
```

**Requirements:**
- Backend must have CORS configured to allow `http://localhost:5173`
- Check `python-backend/main.py` for CORS settings

**How it works:**
- Frontend makes requests to `http://localhost:8000/api/auth/signup`, etc.
- Browser enforces CORS policy
- Backend must explicitly allow the frontend origin

#### 3. Production

**Use Case:** Deployed application

**Configuration:**
```bash
VITE_API_URL=https://api.yourdomain.com/api
```

**Requirements:**
- Backend must be deployed and accessible
- CORS must allow your frontend domain
- HTTPS recommended for production

**How it works:**
- Frontend makes requests to production API
- All requests go to the configured production URL
- Ensure proper CORS and security headers

### Environment-Specific Files

You can create multiple environment files:

```bash
.env                 # Default (used if no other matches)
.env.local           # Local overrides (gitignored)
.env.development     # Development mode
.env.production      # Production mode
```

Vite automatically loads the appropriate file based on the mode.

## Verification Steps

### 1. Check Configuration

```bash
# View your current configuration
cat .env

# Or on Windows
type .env
```

### 2. Verify in Browser

1. Start the development server:
   ```bash
   pnpm dev
   ```

2. Open browser DevTools (F12)

3. Go to Network tab

4. Perform an action that makes an API call (e.g., signup)

5. Check the request URL - it should use your configured base URL

### 3. Test API Endpoints

Test each endpoint to ensure they work:

**Authentication:**
- POST `/api/auth/signup` - Create account
- POST `/api/auth/login` - Login
- POST `/api/auth/logout` - Logout
- GET `/api/auth/session` - Get session
- POST `/api/auth/refresh` - Refresh token

**Academic Profile:**
- POST `/api/academic` - Create profile
- GET `/api/academic` - Get profile
- PUT `/api/academic` - Update profile

**Preferences:**
- POST `/api/preferences` - Create preferences
- GET `/api/preferences` - Get preferences
- PUT `/api/preferences` - Update preferences

## Common Issues

### Issue: API requests fail with CORS error

**Symptom:** Browser console shows CORS policy error

**Solution:**
1. Use same-origin configuration (`VITE_API_URL=/api`)
2. Or configure CORS in backend to allow your frontend origin

### Issue: API requests go to wrong URL

**Symptom:** Network tab shows unexpected URLs

**Solution:**
1. Check `.env` file has correct `VITE_API_URL`
2. Restart dev server (Vite reads env vars at startup)
3. Clear browser cache

### Issue: Environment variable not working

**Symptom:** Changes to `.env` don't take effect

**Solution:**
1. Restart the dev server (required for env var changes)
2. Ensure variable name starts with `VITE_` (Vite requirement)
3. Check for typos in variable name

### Issue: Production build uses wrong API URL

**Symptom:** Built app connects to wrong backend

**Solution:**
1. Set `VITE_API_URL` before building
2. Or use `.env.production` file
3. Rebuild the application

## Code Implementation

### How It Works

All API calls in the application use the configured base URL:

**auth.ts:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// All API calls use this base URL
fetch(`${API_BASE_URL}/auth/signup`, { ... })
fetch(`${API_BASE_URL}/academic`, { ... })
```

**constants.ts:**
```typescript
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
```

**Dashboard.tsx:**
```typescript
import { API_BASE_URL } from "@/lib/constants";

fetch(`${API_BASE_URL}/chat`, { ... })
```

### Adding New API Calls

When adding new API endpoints, always use the configured base URL:

```typescript
import { API_BASE_URL } from "@/lib/constants";

// Good ✓
fetch(`${API_BASE_URL}/new-endpoint`, { ... })

// Bad ✗
fetch('/api/new-endpoint', { ... })
fetch('http://localhost:8000/api/new-endpoint', { ... })
```

## Best Practices

1. **Use relative URLs in development** - Set `VITE_API_URL=/api` for simplest setup

2. **Never commit `.env`** - Keep sensitive configuration out of version control

3. **Document required variables** - Update `.env.example` when adding new variables

4. **Restart after changes** - Always restart dev server after changing `.env`

5. **Test before deploying** - Verify configuration works in production-like environment

6. **Use HTTPS in production** - Always use secure connections for production APIs

## Additional Resources

- [Vite Environment Variables Documentation](https://vitejs.dev/guide/env-and-mode.html)
- [Backend API Documentation](../python-backend/API_ENDPOINTS.md)
- [CORS Configuration Guide](../python-backend/README.md)
