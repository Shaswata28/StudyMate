# StudyMate AI Chat - FastAPI Backend

Python FastAPI backend service for Gemini-powered AI chat functionality.

## Overview

This FastAPI backend integrates Google's Gemini API to provide AI-powered chat capabilities for the StudyMate application. It runs alongside the existing Express server, handling AI chat requests while the Express server manages other application routes.

## Project Structure

```
python-backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── routers/
│   └── chat.py           # Chat endpoint implementation
├── services/
│   └── gemini_service.py # Gemini API integration
├── middleware/
│   ├── rate_limiter.py   # Rate limiting logic
│   └── logging_middleware.py # Request/response logging
└── models/
    └── schemas.py        # Pydantic data models
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd python-backend
python -m venv venv
```

### 2. Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env` and set your `GEMINI_API_KEY`:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 5. Run the Development Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

See `.env.example` for all available configuration options. For comprehensive configuration documentation, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

### Required Variables

- `SUPABASE_URL` - Your Supabase project URL (required)
- `SUPABASE_ANON_KEY` - Supabase anonymous key (required)
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (required)
- `SUPABASE_DB_PASSWORD` - Database password for migrations (required)

### Optional Variables

- `RATE_LIMIT_REQUESTS` - Number of requests allowed per time window (default: 15)
- `RATE_LIMIT_WINDOW` - Time window in seconds (default: 60)
- `ALLOWED_ORIGINS` - CORS allowed origins (default: http://localhost:8080)
- `AI_BRAIN_ENDPOINT` - AI Brain service URL (default: http://localhost:8001)
- `AI_BRAIN_TIMEOUT` - AI Brain request timeout in seconds (default: 300.0)
- `MAX_RETRY_ATTEMPTS` - Maximum retry attempts for transient failures (default: 3)
- `RETRY_DELAY_SECONDS` - Initial retry delay in seconds (default: 2.0)
- `RETRY_BACKOFF_MULTIPLIER` - Exponential backoff multiplier (default: 2.0)

## Database Migrations

The application uses Supabase as the database backend. Before running the application, you need to set up the database schema by running migrations.

### Prerequisites

1. Create a Supabase project at https://supabase.com
2. Get your database credentials from the Supabase dashboard:
   - Project URL: Settings → API → Project URL
   - Anon Key: Settings → API → Project API keys → anon public
   - Service Role Key: Settings → API → Project API keys → service_role (keep secret!)
   - Database Password: Settings → Database → Database password (you set this during project creation)

3. Add these credentials to your `.env` file:
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_DB_PASSWORD=your_database_password_here
```

### Running Migrations

**Forward Migrations** (create tables and schema):
```bash
# Make sure you're in the python-backend directory
cd python-backend

# Activate your virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Run migrations
python scripts/run_migrations.py
```

This will execute the following migrations in order:
1. `001_enable_extensions.sql` - Enable required PostgreSQL extensions (uuid-ossp, pgcrypto, vector, pg_trgm)
2. `002_create_tables.sql` - Create all database tables (academic, personalized, courses, materials, chat_history)
3. `003_create_rls_policies.sql` - Enable Row Level Security and create security policies

**Rollback Migration** (drop all tables):
```bash
python scripts/run_migrations.py --rollback
```

⚠️ **WARNING**: The rollback will drop all tables and data. Use with caution!

### Migration Files

All migration files are located in `python-backend/migrations/`:
- `001_enable_extensions.sql` - PostgreSQL extensions
- `002_create_tables.sql` - Table definitions with constraints and indexes
- `003_create_rls_policies.sql` - Row Level Security policies
- `004_rollback.sql` - Rollback script to drop everything

### Troubleshooting Migrations

**"SUPABASE_DB_PASSWORD not set" Error**:
- Make sure you've added `SUPABASE_DB_PASSWORD` to your `.env` file
- This is your database password from Supabase project settings, not the service role key

**"Connection refused" Error**:
- Verify your Supabase project is active
- Check that your IP address is allowed in Supabase project settings
- Verify the database password is correct

**"Extension already exists" Warnings**:
- These are safe to ignore - the migrations use `IF NOT EXISTS` clauses

**"Permission denied" Errors**:
- Ensure you're using the correct database password
- The postgres user should have full permissions by default

## Testing

Run tests with pytest:

```bash
pytest
```

Run property-based tests:

```bash
pytest -v
```

## AI Brain Service

The backend integrates with a local AI Brain service for material processing (OCR and embedding generation). The AI Brain service must be running for material processing features to work.

### Starting the AI Brain Service

```bash
# In a separate terminal
cd ai-brain
source venv/bin/activate  # Windows: venv\Scripts\activate
python brain.py
```

The AI Brain service will start on port 8001 by default.

### Verifying AI Brain Service

```bash
# Check if service is running
curl http://localhost:8001/

# Should return:
# {"message": "AI Brain Service is running"}
```

### AI Brain Configuration

Configure the AI Brain service endpoint in your `.env` file:

```bash
# Default configuration
AI_BRAIN_ENDPOINT=http://localhost:8001
AI_BRAIN_TIMEOUT=300.0  # 5 minutes for OCR processing
```

For detailed configuration options, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

### What the AI Brain Service Does

- **OCR (Text Extraction)**: Extracts text from PDFs and images using the qwen3-vl:2b model
- **Embedding Generation**: Creates semantic vector embeddings using the mxbai-embed-large model
- **Model Management**: Automatically loads and unloads models to optimize VRAM usage

### Troubleshooting AI Brain Service

**Service Not Starting**:
- Ensure Ollama is installed and running
- Check that required models are downloaded: `ollama list`
- Verify port 8001 is not in use

**Material Processing Failures**:
- Check AI Brain service is running: `curl http://localhost:8001/`
- Review backend logs for connection errors
- Increase timeout for large files: `AI_BRAIN_TIMEOUT=600.0`

For more troubleshooting help, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#troubleshooting).

## Running Both Servers Locally

The StudyMate application requires the Express server (frontend + existing API), the FastAPI backend (AI chat), and the AI Brain service (material processing) to run simultaneously.

### Option 1: Run in Separate Terminals (Recommended for Development)

**Terminal 1 - AI Brain Service:**
```bash
cd ai-brain
source venv/bin/activate  # Windows: venv\Scripts\activate
python brain.py
```

**Terminal 2 - FastAPI Backend:**
```bash
cd python-backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 3 - Express + React Frontend:**
```bash
# From project root
pnpm dev
```

The Express server will automatically proxy `/api/chat` requests to the FastAPI backend during development.

### Option 2: Using Process Managers

You can use tools like `concurrently` or `pm2` to run both servers with a single command. Add to your root `package.json`:

```json
{
  "scripts": {
    "dev:all": "concurrently \"pnpm dev\" \"cd python-backend && uvicorn main:app --reload --port 8000\""
  }
}
```

### Verifying All Services Are Running

1. **AI Brain Service**: Visit `http://localhost:8001/` - should return `{"message": "AI Brain Service is running"}`
2. **FastAPI Backend**: Visit `http://localhost:8000/health` - should return `{"status": "healthy"}`
3. **Express Server**: Visit `http://localhost:8080` - should load the React application
4. **API Docs**: Visit `http://localhost:8000/docs` - should show Swagger UI

## Authentication

The backend uses Supabase Auth for JWT-based authentication. Protected routes require a valid JWT token in the Authorization header.

### Using Authentication in Routes

**Protected Route Example:**
```python
from fastapi import APIRouter, Depends
from services.auth_service import get_current_user, AuthUser

router = APIRouter()

@router.get("/api/profile")
async def get_profile(user: AuthUser = Depends(get_current_user)):
    """Protected route - requires authentication."""
    return {
        "user_id": user.id,
        "email": user.email
    }
```

**Optional Authentication Example:**
```python
from fastapi import APIRouter, Depends
from services.auth_service import get_current_user_optional, AuthUser
from typing import Optional

router = APIRouter()

@router.get("/api/public-or-private")
async def flexible_route(user: Optional[AuthUser] = Depends(get_current_user_optional)):
    """Route that works with or without authentication."""
    if user:
        return {"message": f"Hello {user.email}"}
    else:
        return {"message": "Hello anonymous user"}
```

### Authentication Middleware

Two middleware options are available:

**1. AuthMiddleware (Recommended)** - Enriches requests with user info but doesn't block unauthenticated requests:
```python
from middleware.auth_middleware import AuthMiddleware

app = FastAPI()
app.add_middleware(AuthMiddleware)

# Access user info in routes via request.state
@app.get("/api/example")
async def example(request: Request):
    if request.state.user:
        user_id = request.state.user["id"]
        # User is authenticated
    else:
        # User is not authenticated
```

**2. RequireAuthMiddleware** - Blocks all unauthenticated requests (except public paths):
```python
from middleware.auth_middleware import RequireAuthMiddleware

# Protect entire API
app = FastAPI()
app.add_middleware(RequireAuthMiddleware)

# Or protect specific router
protected_router = APIRouter()
protected_router.add_middleware(RequireAuthMiddleware)
```

### Making Authenticated Requests

**From Frontend:**
```javascript
// Get token from Supabase Auth
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Make authenticated request
const response = await fetch('/api/profile', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

**From Python:**
```python
import httpx

token = "your_jwt_token_here"
headers = {"Authorization": f"Bearer {token}"}

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/profile",
        headers=headers
    )
```

### Authentication Error Responses

**401 Unauthorized** - Missing or invalid token:
```json
{
  "detail": "Invalid or expired authentication token"
}
```

**401 Unauthorized** - Missing token:
```json
{
  "detail": "Missing authentication token"
}
```

## API Endpoint Specifications

### POST /api/chat

Send a message to the AI and receive a response.

**Request:**
```json
{
  "message": "What is photosynthesis?",
  "history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "model",
      "content": "Hi! How can I help you today?"
    }
  ]
}
```

**Request Schema:**
- `message` (string, required): User's message (1-2000 characters)
- `history` (array, optional): Conversation history (max 10 messages)
  - `role` (string): Either "user" or "model"
  - `content` (string): Message content

**Success Response (200):**
```json
{
  "response": "Photosynthesis is the process by which plants...",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Error Responses:**

**400 Bad Request** - Invalid input:
```json
{
  "error": "Validation error",
  "code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "message",
      "message": "Message must be between 1 and 2000 characters"
    }
  ]
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "error": "You've reached the message limit. Please try again in a moment.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

**500 Internal Server Error** - Server error:
```json
{
  "error": "Something went wrong. Please try again.",
  "code": "INTERNAL_ERROR"
}
```

**503 Service Unavailable** - Gemini API error:
```json
{
  "error": "I'm having trouble connecting right now. Please try again.",
  "code": "GEMINI_API_ERROR"
}
```

### GET /health

Health check endpoint to verify the service is running.

**Success Response (200):**
```json
{
  "status": "healthy"
}
```

### Rate Limiting

- **Default Limit**: 15 requests per 60 seconds per IP address
- **Headers**: Responses include rate limit information:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Time when the limit resets

## Development

The server supports hot-reload in development mode. Any changes to Python files will automatically restart the server.

### Development Tips

1. **Check Logs**: The FastAPI backend logs all requests, errors, and Gemini API calls to the console
2. **Interactive API Docs**: Use `http://localhost:8000/docs` to test endpoints interactively
3. **CORS**: In development, the backend accepts requests from `http://localhost:8080` by default
4. **Rate Limiting**: You can adjust rate limits in `.env` for testing purposes

## Troubleshooting

### "GEMINI_API_KEY not found" Error

Make sure you've created a `.env` file in the `python-backend/` directory with your API key:
```bash
cp .env.example .env
# Edit .env and add your actual API key
```

### Port Already in Use

If port 8000 is already in use, you can run on a different port:
```bash
uvicorn main:app --reload --port 8001
```

Remember to update the proxy configuration in `vite.config.ts` if you change the port.

### CORS Errors

If you see CORS errors in the browser console:
1. Verify the FastAPI backend is running on port 8000
2. Check that `ALLOWED_ORIGINS` in `.env` includes `http://localhost:8080`
3. Restart both servers after changing environment variables

### Rate Limit Testing

To test rate limiting without waiting, temporarily reduce the limits in `.env`:
```
RATE_LIMIT_REQUESTS=3
RATE_LIMIT_WINDOW=10
```

## Production Deployment

### Environment Variables

Ensure all required environment variables are set in your production environment:
- `GEMINI_API_KEY` - Your production Gemini API key
- `ALLOWED_ORIGINS` - Your production frontend URL (e.g., `https://studymate.com`)
- Adjust rate limits as needed for production traffic

### Running in Production

```bash
# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Optional)

Create a `Dockerfile` in the `python-backend/` directory:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t studymate-backend .
docker run -p 8000:8000 --env-file .env studymate-backend
```
