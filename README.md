# StudyMate 📚🤖

An AI-powered study assistant that provides personalized academic support using locally-hosted AI models. Built with React, FastAPI, and Ollama for privacy-focused, offline-capable learning assistance.

## ✨ Features

- **Personalized AI Tutoring** - Adapts responses based on your academic level, subject, and learning preferences
- **Course Management** - Organize study materials by course with dedicated chat contexts
- **RAG-Powered Responses** - Retrieves relevant course materials to provide accurate, contextual answers
- **Document Processing** - Upload PDFs and images for AI-powered analysis and extraction
- **Voice Input** - Speech-to-text support using Web Speech API
- **Multi-Turn Conversations** - Maintains context across chat sessions
- **Dark/Light Theme** - Comfortable studying in any environment
- **Fully Local AI** - All AI processing runs locally via Ollama for privacy and offline use

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│              Vite + TypeScript + TailwindCSS + Radix UI         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Node.js Express Server                       │
│                    (API Proxy & Static Files)                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Python Backend (FastAPI)                      │
│         Auth • Chat • Courses • RAG • Intent Classification     │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────┐     ┌───────────────────────────────┐
│      AI Brain Service     │     │         Supabase              │
│         (Ollama)          │     │   PostgreSQL + Auth + Vector  │
│  • StudyMate-core (Chat)  │     │                               │
│  • qwen2.5vl (Vision)     │     │                               │
│  • mxbai-embed (RAG)      │     │                               │
└───────────────────────────┘     └───────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- [Ollama](https://ollama.ai/)
- [Supabase](https://supabase.com/) account

### Installation

```bash
# Automated (recommended)
./install.sh          # Linux/macOS
install.bat           # Windows
python install_dependencies.py  # All platforms

# Manual
pnpm install                              # Frontend
cd python-backend && pip install -r requirements.txt  # Backend
cd ai-brain && pip install -r requirements.txt        # AI Brain
```

### Configuration

1. Copy environment files:
```bash
cp .env.example .env
cp python-backend/.env.example python-backend/.env
```

2. Add your Supabase credentials to both `.env` files

3. Pull Ollama models:
```bash
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
ollama create Studymate-core -f Modelfile.updated
```

### Running

```bash
# Terminal 1: AI Brain (port 8001)
cd ai-brain && python brain.py

# Terminal 2: Python Backend (port 8000)
cd python-backend && uvicorn main:app --reload

# Terminal 3: Frontend (port 8080)
pnpm dev
```

Open http://localhost:8080

## 📁 Project Structure

```
studymate/
├── client/                 # React frontend
│   ├── components/         # UI components (Chat, Sidebar, Modals)
│   ├── pages/              # Route pages (Dashboard, Login, Signup)
│   └── lib/                # Utilities and API client
├── python-backend/         # FastAPI backend
│   ├── routers/            # API endpoints (auth, chat, courses)
│   ├── services/           # Business logic (AI, RAG, context)
│   └── models/             # Pydantic schemas
├── ai-brain/               # Local AI service (Ollama orchestration)
├── server/                 # Node.js Express proxy
├── Dataset/                # Training data for fine-tuning
└── Documentation/          # Project docs
```


## 🤖 AI Models

| Model | Purpose | Size |
|-------|---------|------|
| StudyMate-core | Main chat model (fine-tuned) | ~4GB |
| qwen2.5vl:3b | Vision/OCR for PDFs & images | ~2GB |
| mxbai-embed-large | Text embeddings for RAG | ~670MB |

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/session` - Get session

### Chat
- `POST /api/chat` - Global chat
- `POST /api/chat/{course_id}` - Course-specific chat

### Courses
- `GET /api/courses` - List courses
- `POST /api/courses` - Create course
- `DELETE /api/courses/{id}` - Delete course
- `POST /api/courses/{id}/materials` - Upload materials

### Academic Profile
- `GET /api/academic` - Get profile
- `POST /api/academic` - Create profile
- `PUT /api/academic` - Update profile

## 🛠️ Tech Stack

**Frontend:** React 18, TypeScript, Vite, TailwindCSS, Radix UI, React Query, Framer Motion

**Backend:** FastAPI, Supabase (PostgreSQL + Auth + Vector), Pydantic

**AI:** Ollama, Custom fine-tuned models, RAG with vector embeddings

## 🧪 Development

```bash
pnpm dev          # Start frontend dev server
pnpm test         # Run frontend tests
pnpm typecheck    # TypeScript validation
pnpm format.fix   # Format code

# Backend tests
cd python-backend && pytest
```

## 📖 Documentation

See the `Documentation/` folder for detailed guides:
- [Installation Guide](Documentation/INSTALLATION.md)
- [Backend Flow](Documentation/BACKEND_FLOW_EXPLAINED.md)
- [RAG Verification](Documentation/RAG_VERIFICATION_GUIDE.md)

---

Built with ❤️ for students who want AI-powered study assistance without compromising privacy.
