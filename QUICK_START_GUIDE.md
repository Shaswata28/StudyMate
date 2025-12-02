# 🚀 StudyMate Quick Start Guide

## Prerequisites

- Python 3.10+ installed
- Node.js 16+ installed
- pnpm installed (`npm install -g pnpm`)
- Supabase account with project created

---

## Setup Steps

### 1. Install Dependencies

**Backend:**
```bash
cd python-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install email-validator  # Important!
```

**Frontend:**
```bash
# From project root
pnpm install
```

### 2. Configure Environment Variables

**Backend** (`python-backend/.env`):
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Gemini API (for AI chat)
GEMINI_API_KEY=your_gemini_api_key

# CORS (for development)
ALLOWED_ORIGINS=http://localhost:8080
```

**Frontend** (`.env` in project root):
```env
# Optional - defaults to /api
VITE_API_URL=http://localhost:8000/api
```

### 3. Set Up Database

Run the database migrations:
```bash
cd python-backend
python scripts/run_migrations.py
```

---

## Running the Application

### Start Backend (Terminal 1)
```bash
cd python-backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Backend will run on: `http://localhost:8000`

### Start Frontend (Terminal 2)
```bash
# From project root
pnpm dev
```

Frontend will run on: `http://localhost:8080`

---

## First Time User Flow

### 1. Create Account
1. Visit `http://localhost:8080/signup`
2. Enter email and password (Step 1)
3. Fill in academic profile (Step 2)
4. Complete learning preferences questionnaire
5. You'll be redirected to the dashboard

### 2. Create Your First Course
1. Click "New Course" in the sidebar
2. Enter course name (e.g., "Biology 101")
3. Pick a color
4. Click "Create Course"
5. Course appears in sidebar!

### 3. Start Chatting
1. Select your course from sidebar
2. Type a question in the chat
3. Optionally attach files (PDFs, images)
4. Get AI-powered responses

---

## Key Features

### ✅ Authentication
- User registration with email/password
- JWT-based authentication
- Automatic token refresh
- Secure session management

### ✅ Course Management
- Create unlimited courses
- Organize by color
- Switch between courses
- Each course has separate chat history

### ✅ AI Chat
- Powered by Google Gemini
- Context-aware responses
- File attachment support (PDFs, images)
- Conversation history
- Personalized based on your preferences

### ✅ User Profile
- View account information
- See member since date
- Access settings
- Help & FAQ section

---

## API Documentation

Once backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Troubleshooting

### Backend Won't Start

**Error: "email-validator not installed"**
```bash
pip install email-validator
```

**Error: "SUPABASE_URL not set"**
- Check `python-backend/.env` file exists
- Verify all Supabase credentials are set

**Error: "Port 8000 already in use"**
```bash
# Use different port
uvicorn main:app --reload --port 8001
```

### Frontend Won't Start

**Error: "Cannot find module"**
```bash
pnpm install
```

**Error: "CORS error"**
- Verify backend is running
- Check `ALLOWED_ORIGINS` in backend `.env`

### Database Issues

**Error: "Connection refused"**
- Verify Supabase project is active
- Check database credentials
- Ensure IP is whitelisted in Supabase

**Error: "Table does not exist"**
```bash
cd python-backend
python scripts/run_migrations.py
```

### Authentication Issues

**Can't log in after signup**
- Check backend logs for errors
- Verify Supabase Auth is enabled
- Try creating user directly in Supabase dashboard

**Token expired errors**
- Tokens auto-refresh
- If persistent, log out and log back in
- Check backend logs for refresh errors

---

## Development Tips

### Hot Reload
Both servers support hot reload:
- Backend: Changes to `.py` files auto-restart
- Frontend: Changes to `.tsx` files auto-refresh

### Debugging

**Backend Logs:**
```bash
# Backend terminal shows all requests
INFO:     127.0.0.1:xxxxx - "POST /api/courses HTTP/1.1" 201 Created
```

**Frontend Console:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for API calls

**Database:**
- Use Supabase dashboard to view tables
- Check Table Editor for data
- Use SQL Editor for queries

### Testing API Endpoints

Use the Swagger UI at `http://localhost:8000/docs`:
1. Click on an endpoint
2. Click "Try it out"
3. Fill in parameters
4. Click "Execute"
5. See response

---

## Project Structure

```
StudyMate/
├── client/                 # React frontend
│   ├── components/        # UI components
│   ├── pages/            # Page components
│   ├── hooks/            # Custom React hooks
│   └── lib/              # Services & utilities
│       ├── auth.ts       # Authentication service
│       ├── courses.ts    # Course service
│       └── toast.ts      # Toast notifications
│
├── python-backend/        # FastAPI backend
│   ├── routers/          # API route handlers
│   │   ├── auth.py       # Auth endpoints
│   │   ├── courses.py    # Course endpoints
│   │   ├── chat.py       # Chat endpoints
│   │   └── ...
│   ├── services/         # Business logic
│   ├── models/           # Data models
│   ├── middleware/       # Middleware
│   └── migrations/       # Database migrations
│
└── docs/                 # Documentation
```

---

## Common Tasks

### Add a New API Endpoint

1. Create route in `python-backend/routers/`
2. Add schema in `python-backend/models/schemas.py`
3. Register router in `python-backend/main.py`
4. Create service method in `client/lib/`
5. Use in React components

### Add a New Page

1. Create component in `client/pages/`
2. Add route in `client/App.tsx`
3. Use `<ProtectedRoute>` if auth required

### Update Database Schema

1. Create migration SQL in `python-backend/migrations/`
2. Run migration script
3. Update Pydantic models if needed

---

## Support

### Documentation
- `COURSE_INTEGRATION_COMPLETE.md` - Course & user info integration
- `BACKEND_INTEGRATION_COMPLETE.md` - Backend setup
- `client/lib/AUTH_README.md` - Authentication guide
- `python-backend/README.md` - Backend documentation

### Getting Help
- Check browser console for frontend errors
- Check terminal for backend errors
- Review API docs at `/docs`
- Check Supabase dashboard for database issues

---

## What's Next?

Now that you have the basics working, you can:

1. **Upload Materials** - Implement file upload to courses
2. **Chat History** - Save conversations to database
3. **Search** - Add course search functionality
4. **Analytics** - Track learning progress
5. **Sharing** - Share courses with others
6. **Mobile App** - Build mobile version

Happy coding! 🎉
