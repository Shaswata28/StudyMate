# StudyMate

An AI-powered study assistant application with React frontend and FastAPI backend.

## Quick Start

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

### Quick Installation

**Windows:**
```bash
install.bat
```

**macOS/Linux:**
```bash
chmod +x install.sh
./install.sh
```

**All platforms:**
```bash
python install_dependencies.py
```

## Project Structure

- `client/` - React frontend application
- `python-backend/` - FastAPI backend server
- `docs/` - Project documentation
- `.kiro/specs/` - Feature specifications

## Documentation

### Getting Started
- [Installation Guide](INSTALLATION.md) - Complete setup instructions
- [Environment Setup](docs/ENVIRONMENT_SETUP.md) - Environment variable configuration

### Registration & Authentication
- [Registration Flow](docs/REGISTRATION_FLOW.md) - Complete registration flow documentation
- [API Reference](docs/API_REFERENCE.md) - Detailed API endpoint documentation
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Database & Backend
- [Database Schema](docs/database-schema.md) - Database structure
- [API Endpoints](python-backend/API_ENDPOINTS.md) - Backend API documentation
- [Supabase Setup](docs/SUPABASE_SETUP.md) - Database configuration

## Environment Configuration

### Frontend Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Frontend API Configuration
# The base URL for API requests from the frontend
VITE_API_URL=/api  # Development (default)
# VITE_API_URL=http://localhost:8000/api  # Alternative development
# VITE_API_URL=https://your-api-domain.com/api  # Production
```

**Configuration Options:**

- **Development (default)**: `VITE_API_URL=/api`
  - Uses relative URLs, works with Vite proxy or same-origin deployment
  - Recommended for most development scenarios

- **Development (explicit)**: `VITE_API_URL=http://localhost:8000/api`
  - Use when running frontend and backend on different ports
  - Requires CORS configuration in backend

- **Production**: `VITE_API_URL=https://your-api-domain.com/api`
  - Set to your production API domain
  - Ensure CORS is properly configured

**Note**: All frontend API calls automatically use the configured `VITE_API_URL`. The variable is read at build time, so restart the dev server after changes.

### Backend Environment Variables

See [python-backend/.env.example](python-backend/.env.example) for backend configuration.

## Development

```bash
# Frontend (Terminal 1)
pnpm dev

# Backend (Terminal 2)
cd python-backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload
```

### Testing with Different Environment Configurations

**Local Development (Same Origin):**
```bash
# .env
VITE_API_URL=/api

# Run both frontend and backend
pnpm dev  # Frontend on port 5173
cd python-backend && uvicorn main:app --reload  # Backend on port 8000
```

**Local Development (Different Ports):**
```bash
# .env
VITE_API_URL=http://localhost:8000/api

# Ensure CORS is configured in python-backend/main.py
# Run both services
pnpm dev
cd python-backend && uvicorn main:app --reload
```

**Production Testing:**
```bash
# .env
VITE_API_URL=https://your-api-domain.com/api

# Build and test
pnpm build
pnpm preview
```

**Verifying Configuration:**
1. Check browser console for API request URLs
2. Verify all requests use the configured base URL
3. Test authentication flow (signup, login, logout)
4. Test academic profile and preferences endpoints

## Registration Flow

StudyMate implements a three-step registration process:

### Step 1: Security Credentials
Users provide basic account information:
- Email address
- Password (minimum 8 characters)
- Full name
- Terms acceptance

### Step 2: Academic Profile
Users provide educational context:
- Grade level (Bachelor, Masters, PhD, etc.)
- Semester type (Double or Tri)
- Current semester number
- Subject areas of study

### Step 3: Learning Preferences
Users customize their learning experience through an onboarding questionnaire:
- Detail level, examples, analogies preferences
- Technical language preference
- Learning pace and prior experience

**Complete Documentation:** See [Registration Flow Guide](docs/REGISTRATION_FLOW.md) for detailed architecture, data flow, and implementation details.

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new account
- `POST /api/auth/login` - Login existing user
- `POST /api/auth/logout` - Logout current user
- `GET /api/auth/session` - Get current session
- `POST /api/auth/refresh` - Refresh access token

### Academic Profile
- `POST /api/academic` - Create academic profile
- `GET /api/academic` - Retrieve academic profile
- `PUT /api/academic` - Update academic profile

### Preferences
- `POST /api/preferences` - Create/update preferences
- `GET /api/preferences` - Retrieve preferences
- `PUT /api/preferences` - Update preferences

**Complete API Documentation:** See [API Reference](docs/API_REFERENCE.md) for request/response formats, error codes, and examples.

## Error Handling

The application implements comprehensive error handling:

| Error Code | Description | Example |
|------------|-------------|---------|
| 400 | Validation error | "A user with this email already exists" |
| 401 | Authentication error | "Invalid or expired authentication token" |
| 403 | Authorization error | "Not authenticated" |
| 409 | Conflict error | "Academic profile already exists" |
| 422 | Validation error | "Password must be at least 8 characters" |
| 500 | Server error | "An unexpected error occurred" |

All errors are displayed via toast notifications with clear, user-friendly messages.

**Troubleshooting:** See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for solutions to common issues.

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Radix UI
- **Backend**: FastAPI, Python 3.8+
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT-based with Supabase Auth
- **AI**: Local AI Brain Service (Qwen 2.5, DeepSeek OCR, Whisper Turbo, mxbai-embed-large)
- **Package Manager**: pnpm